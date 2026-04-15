"""
FastAPI routes for the Parser Engine.

Endpoints:
    POST /parse                 — parse a single configuration
    POST /parse/batch           — parse multiple configurations
    POST /detect-vendor         — detect vendor without full parse
    GET  /vendors               — list supported vendors
    GET  /health                — module health check
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..models.device import ParsedDevice, VendorType
from ..parsers.base_parser import ParserError, VendorDetectionError
from ..services.parsing_service import ParsingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parser", tags=["parser"])

# Module-level service instance (no Redis in API layer — injected by main app if desired)
_service = ParsingService()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ParseRequest(BaseModel):
    """Request body for a single configuration parse."""

    config: str = Field(..., min_length=1, description="Raw device configuration text")
    vendor: Optional[VendorType] = Field(
        None, description="Vendor hint — skip auto-detection when set"
    )

    model_config = {"json_schema_extra": {"example": {
        "config": "hostname ROUTER-01\ninterface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n!",
        "vendor": "cisco_ios",
    }}}


class BatchParseRequest(BaseModel):
    """Request body for batch parsing."""

    configs: list[str] = Field(..., min_length=1, description="List of raw configurations")
    vendor: Optional[VendorType] = Field(None, description="Common vendor hint for all configs")


class VendorDetectRequest(BaseModel):
    """Request body for vendor detection."""

    config: str = Field(..., min_length=1, description="Raw device configuration text")


class VendorDetectResponse(BaseModel):
    """Response body for vendor detection."""

    vendor: str = Field(..., description="Detected vendor identifier")
    confidence: str = Field(default="high", description="Detection confidence level")


class SupportedVendorsResponse(BaseModel):
    """Response listing supported vendor parsers."""

    vendors: list[str] = Field(..., description="Supported vendor identifiers")
    count: int = Field(..., description="Number of supported vendors")


class HealthResponse(BaseModel):
    """Parser engine health check response."""

    status: str
    module: str
    version: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse, summary="Parser Engine health check")
async def health_check() -> HealthResponse:
    """
    Return the operational status of the Parser Engine module.
    """
    return HealthResponse(
        status="healthy",
        module="parser_engine",
        version="1.0.0",
    )


@router.get(
    "/vendors",
    response_model=SupportedVendorsResponse,
    summary="List supported vendors",
)
async def list_vendors() -> SupportedVendorsResponse:
    """
    Return the list of network vendor / OS parsers currently registered.
    """
    vendors = _service.list_supported_vendors()
    return SupportedVendorsResponse(vendors=vendors, count=len(vendors))


@router.post(
    "/detect-vendor",
    response_model=VendorDetectResponse,
    summary="Detect vendor from configuration",
)
async def detect_vendor(request: VendorDetectRequest) -> VendorDetectResponse:
    """
    Quickly identify the vendor / OS type from the supplied configuration
    without performing a full parse.

    Returns a vendor identifier string (e.g. ``cisco_ios``, ``fortinet_fortios``).
    """
    try:
        vendor = _service.detect_vendor(request.config)
    except VendorDetectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return VendorDetectResponse(vendor=vendor.value)


@router.post(
    "/parse",
    response_model=ParsedDevice,
    summary="Parse a device configuration",
    status_code=status.HTTP_200_OK,
)
async def parse_config(request: ParseRequest) -> ParsedDevice:
    """
    Parse a single network device configuration.

    The parser is auto-selected based on configuration fingerprints unless
    the ``vendor`` field is provided as a hint.

    Returns a ``ParsedDevice`` containing:
    - ``device``: the fully parsed device model
    - ``parser_version``: version of the parser used
    - ``parsing_duration_ms``: elapsed parsing time
    - ``warnings``: non-fatal anomalies
    - ``errors``: fatal errors (empty list = success)
    """
    try:
        result = await _service.parse(request.config, vendor=request.vendor)
    except VendorDetectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Vendor detection failed: {exc}",
        ) from exc
    except ParserError as exc:
        logger.error("Parse error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parsing failed: {exc}",
        ) from exc

    return result


@router.post(
    "/parse/batch",
    response_model=list[ParsedDevice],
    summary="Parse multiple configurations",
    status_code=status.HTTP_200_OK,
)
async def parse_batch(request: BatchParseRequest) -> list[ParsedDevice]:
    """
    Parse a list of device configurations in a single request.

    Useful for bulk imports. Each config is parsed independently;
    a failure in one does not prevent others from being attempted.

    Returns an ordered list of ``ParsedDevice`` objects.
    """
    try:
        results = await _service.parse_batch(request.configs, vendor=request.vendor)
    except (VendorDetectionError, ParserError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return results
