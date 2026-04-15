"""
Abstract base parser — all vendor parsers must implement this interface.
"""
from __future__ import annotations

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from ..models.device import Device, ParsedDevice, VendorType

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Raised when a fatal parsing error occurs."""

    def __init__(self, message: str, vendor: Optional[str] = None, line: Optional[int] = None):
        self.vendor = vendor
        self.line = line
        super().__init__(message)


class VendorDetectionError(ParserError):
    """Raised when the vendor / OS type cannot be determined."""


class BaseParser(ABC):
    """
    Abstract base class for all network device configuration parsers.

    Subclasses must implement:
        - ``vendor``: class-level VendorType attribute.
        - ``can_parse``: quick check to see if this parser can handle the config.
        - ``_do_parse``: the actual parsing logic.

    Usage::

        parser = CiscoIOSParser()
        result: ParsedDevice = await parser.parse(raw_config)
    """

    # Subclasses must declare their vendor
    vendor: VendorType = VendorType.UNKNOWN

    # Parser version — bump when the regex/logic changes to invalidate old cache entries
    parser_version: str = "1.0.0"

    def __init__(self, strict_mode: bool = False) -> None:
        """
        Initialise the parser.

        Args:
            strict_mode: When True, unknown stanzas raise ParserError instead of
                         being silently skipped.
        """
        self.strict_mode = strict_mode
        self._warnings: list[str] = []
        self._errors: list[str] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def parse(self, raw_config: str) -> ParsedDevice:
        """
        Parse a raw configuration string and return a ParsedDevice.

        Args:
            raw_config: Full text of the device configuration.

        Returns:
            ParsedDevice containing the parsed Device plus metadata.

        Raises:
            ParserError: On fatal parsing failure.
        """
        self._warnings = []
        self._errors = []

        if not raw_config or not raw_config.strip():
            raise ParserError("Configuration is empty", vendor=self.vendor.value)

        logger.debug("Starting parse [vendor=%s, size=%d bytes]", self.vendor.value, len(raw_config))
        start_ts = time.monotonic()

        try:
            device = await self._do_parse(raw_config)
        except ParserError:
            raise
        except Exception as exc:
            raise ParserError(
                f"Unexpected error during parsing: {exc}", vendor=self.vendor.value
            ) from exc

        duration_ms = (time.monotonic() - start_ts) * 1000
        logger.info(
            "Parsed [vendor=%s, hostname=%s, ifaces=%d, dur=%.1f ms]",
            self.vendor.value,
            device.hostname,
            len(device.interfaces),
            duration_ms,
        )

        return ParsedDevice(
            device=device,
            parser_version=self.parser_version,
            parsing_duration_ms=round(duration_ms, 2),
            warnings=list(self._warnings),
            errors=list(self._errors),
        )

    @abstractmethod
    def can_parse(self, raw_config: str) -> bool:
        """
        Quickly determine whether this parser can handle the given configuration.

        This method must be fast (no heavy regex) since it is called for every
        registered parser during auto-detection.

        Args:
            raw_config: First few lines or full configuration text.

        Returns:
            True when this parser is likely compatible.
        """

    @abstractmethod
    async def _do_parse(self, raw_config: str) -> Device:
        """
        Core parsing implementation.

        Args:
            raw_config: Full configuration text.

        Returns:
            Fully populated Device model.
        """

    # ------------------------------------------------------------------
    # Helper utilities available to subclasses
    # ------------------------------------------------------------------

    def _warn(self, message: str) -> None:
        """Record a non-fatal parsing warning."""
        logger.warning("[%s] %s", self.vendor.value, message)
        self._warnings.append(message)

    def _error(self, message: str) -> None:
        """Record a fatal parsing error (stored but does not raise)."""
        logger.error("[%s] %s", self.vendor.value, message)
        self._errors.append(message)

    @staticmethod
    def config_fingerprint(raw_config: str) -> str:
        """
        Compute a deterministic fingerprint for a configuration blob.

        Used as a cache key so identical configs are not re-parsed.

        Args:
            raw_config: Full configuration text.

        Returns:
            Hex-encoded SHA-256 digest string.
        """
        return hashlib.sha256(raw_config.encode("utf-8")).hexdigest()

    @staticmethod
    def split_blocks(config: str, delimiter: str = "!") -> list[str]:
        """
        Split a configuration into logical blocks separated by *delimiter*.

        Args:
            config: Full configuration text.
            delimiter: Block separator character (default ``!`` for Cisco).

        Returns:
            List of non-empty block strings.
        """
        blocks = config.split(delimiter)
        return [b.strip() for b in blocks if b.strip()]

    @staticmethod
    def extract_lines(block: str) -> list[str]:
        """
        Return the non-empty, non-comment lines from a config block.

        Args:
            block: A single configuration stanza or the full config.

        Returns:
            List of stripped lines excluding blank lines and ``!`` comment lines.
        """
        return [
            line.rstrip()
            for line in block.splitlines()
            if line.strip() and not line.strip().startswith("!")
        ]
