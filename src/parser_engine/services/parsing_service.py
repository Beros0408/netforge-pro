"""
Parsing service — orchestrates vendor detection, parser selection, and
optional Redis caching of parsed results.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from ..config import settings
from ..models.device import ParsedDevice, VendorType
from ..parsers.base_parser import BaseParser, ParserError, VendorDetectionError
from ..parsers.cisco.ios_parser import CiscoIOSParser
from ..parsers.fortinet.fortios_parser import FortiOSParser
from ..parsers.huawei.vrp_parser import HuaweiVRPParser
from ..parsers.arista.eos_parser import AristaEOSParser

logger = logging.getLogger(__name__)

# Registry of all available parsers (ordered by priority)
_PARSER_REGISTRY: list[type[BaseParser]] = [
    CiscoIOSParser,
    FortiOSParser,
    HuaweiVRPParser,
    AristaEOSParser,
]


class ParsingService:
    """
    High-level service that selects the appropriate parser for a configuration,
    runs it, and manages a Redis cache to avoid redundant work.

    Usage::

        service = ParsingService()
        result = await service.parse(raw_config)

    Or with an explicit vendor hint::

        result = await service.parse(raw_config, vendor=VendorType.CISCO_IOS)
    """

    def __init__(self, redis_client=None, strict_mode: bool = False) -> None:
        """
        Initialise the ParsingService.

        Args:
            redis_client: An async Redis client (e.g. from ``redis.asyncio``).
                          When None, caching is disabled regardless of settings.
            strict_mode: Propagated to parsers; raises on unrecognised stanzas.
        """
        self._redis = redis_client
        self._strict_mode = strict_mode
        self._cache_enabled = settings.cache_enabled and redis_client is not None
        self._cache_ttl = settings.cache_ttl_seconds

        # Instantiate all registered parsers once
        self._parsers: list[BaseParser] = [
            cls(strict_mode=strict_mode) for cls in _PARSER_REGISTRY
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def parse(
        self,
        raw_config: str,
        vendor: Optional[VendorType] = None,
    ) -> ParsedDevice:
        """
        Parse a device configuration, optionally enforcing a specific vendor.

        The method:
        1. Checks the Redis cache (if enabled).
        2. Auto-detects the vendor unless *vendor* is specified.
        3. Runs the matching parser.
        4. Stores the result in cache.

        Args:
            raw_config: Full text of the device configuration.
            vendor: Optional vendor hint to skip auto-detection.

        Returns:
            ParsedDevice with the parsed device and metadata.

        Raises:
            VendorDetectionError: When no parser can handle the config.
            ParserError: On fatal parsing failure.
        """
        if not raw_config or not raw_config.strip():
            raise ParserError("Empty configuration provided")

        cache_key = self._make_cache_key(raw_config)

        # Cache read
        cached = await self._cache_get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for config fingerprint %s", cache_key[:12])
            return cached

        # Parser selection
        parser = self._select_parser(raw_config, vendor)
        logger.info(
            "Selected parser: %s (vendor=%s)", type(parser).__name__, parser.vendor.value
        )

        # Parse
        result = await parser.parse(raw_config)

        # Cache write
        await self._cache_set(cache_key, result)

        return result

    async def parse_batch(
        self,
        configs: list[str],
        vendor: Optional[VendorType] = None,
    ) -> list[ParsedDevice]:
        """
        Parse multiple configurations sequentially.

        Args:
            configs: List of raw configuration strings.
            vendor: Optional vendor hint applied to all configs.

        Returns:
            List of ParsedDevice results in the same order as *configs*.
        """
        results: list[ParsedDevice] = []
        for config in configs:
            try:
                result = await self.parse(config, vendor=vendor)
            except ParserError as exc:
                logger.error("Batch parse failure: %s", exc)
                raise
            results.append(result)
        return results

    def detect_vendor(self, raw_config: str) -> VendorType:
        """
        Detect the vendor / OS type without performing a full parse.

        Args:
            raw_config: Full configuration text.

        Returns:
            Detected VendorType.

        Raises:
            VendorDetectionError: When no registered parser claims the config.
        """
        for parser in self._parsers:
            if parser.can_parse(raw_config):
                return parser.vendor
        raise VendorDetectionError(
            "Unable to detect vendor — no registered parser matched the configuration"
        )

    def list_supported_vendors(self) -> list[str]:
        """
        Return the list of vendor identifiers supported by registered parsers.

        Returns:
            List of VendorType string values.
        """
        return [p.vendor.value for p in self._parsers]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _select_parser(
        self, raw_config: str, vendor: Optional[VendorType]
    ) -> BaseParser:
        """
        Select the best parser for *raw_config*.

        When *vendor* is given, an exact match is required.
        Otherwise, parsers are tried in registry order using can_parse().

        Args:
            raw_config: Full configuration text.
            vendor: Optional forced vendor.

        Returns:
            Matching BaseParser instance.

        Raises:
            VendorDetectionError: When no parser matches.
        """
        if vendor is not None:
            for parser in self._parsers:
                if parser.vendor == vendor:
                    return parser
            raise VendorDetectionError(
                f"No parser registered for vendor '{vendor.value}'"
            )

        for parser in self._parsers:
            if parser.can_parse(raw_config):
                return parser

        raise VendorDetectionError(
            "No parser could handle the provided configuration. "
            f"Supported vendors: {self.list_supported_vendors()}"
        )

    @staticmethod
    def _make_cache_key(raw_config: str) -> str:
        """Build a Redis cache key from the config fingerprint."""
        fingerprint = BaseParser.config_fingerprint(raw_config)
        return f"netforge:parser:{fingerprint}"

    async def _cache_get(self, key: str) -> Optional[ParsedDevice]:
        """Attempt to retrieve a ParsedDevice from the Redis cache."""
        if not self._cache_enabled or self._redis is None:
            return None
        try:
            raw = await self._redis.get(key)
            if raw:
                data = json.loads(raw)
                return ParsedDevice.model_validate(data)
        except Exception as exc:
            logger.warning("Cache read error: %s", exc)
        return None

    async def _cache_set(self, key: str, result: ParsedDevice) -> None:
        """Store a ParsedDevice in the Redis cache."""
        if not self._cache_enabled or self._redis is None:
            return
        try:
            await self._redis.setex(
                key,
                self._cache_ttl,
                result.model_dump_json(),
            )
        except Exception as exc:
            logger.warning("Cache write error: %s", exc)
