"""
Discovery Engine API routes.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..config import settings
from ..models.discovery import (
    ScanRequest, ScanResult, AutoDiscoveryRequest, DiscoveredDevice,
    DiscoveryStatus
)
from ..services.scanner import NetworkScanner
from ..services.snmp_discovery import SNMPDiscovery
from ..services.fingerprinter import DeviceFingerprinter
from ..services.topology import TopologyDiscovery


# In-memory storage for scan results (in production, use Redis/database)
_scan_results = {}


class ScanResponse(BaseModel):
    """Response for scan operations."""
    scan_id: str
    status: DiscoveryStatus
    message: str


class ScanStatusResponse(BaseModel):
    """Response for scan status queries."""
    scan_id: str
    status: DiscoveryStatus
    progress: dict
    devices_found: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def start_network_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks
) -> ScanResponse:
    """
    Start a network discovery scan.

    This endpoint initiates a network scan with the specified parameters
    and returns immediately with a scan ID for status tracking.
    """
    # Generate scan ID
    scan_id = str(uuid.uuid4())

    # Create scan result object
    scan_result = ScanResult(
        scan_id=scan_id,
        request=request,
        status=DiscoveryStatus.PENDING
    )

    # Store scan result
    _scan_results[scan_id] = scan_result

    # Start background scan
    background_tasks.add_task(_perform_scan, scan_id)

    return ScanResponse(
        scan_id=scan_id,
        status=DiscoveryStatus.PENDING,
        message="Scan started successfully"
    )


@router.get("/scan/{scan_id}", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str) -> ScanStatusResponse:
    """
    Get the status of a network scan.

    Returns the current status, progress, and results of the specified scan.
    """
    if scan_id not in _scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan_result = _scan_results[scan_id]

    return ScanStatusResponse(
        scan_id=scan_result.scan_id,
        status=scan_result.status,
        progress=scan_result.progress,
        devices_found=len(scan_result.devices),
        started_at=scan_result.started_at,
        completed_at=scan_result.completed_at,
        duration_seconds=scan_result.duration_seconds
    )


@router.get("/scan/{scan_id}/devices", response_model=List[DiscoveredDevice])
async def get_scan_devices(scan_id: str) -> List[DiscoveredDevice]:
    """
    Get the devices discovered in a scan.

    Returns the complete list of discovered devices with all available information.
    """
    if scan_id not in _scan_results:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan_result = _scan_results[scan_id]
    return scan_result.devices


@router.post("/auto-discover", response_model=ScanResponse)
async def start_auto_discovery(
    request: AutoDiscoveryRequest,
    background_tasks: BackgroundTasks
) -> ScanResponse:
    """
    Start automatic network discovery from a seed device.

    This endpoint performs topology discovery starting from a seed device
    and automatically discovers the network using LLDP/CDP protocols.
    """
    # Generate scan ID
    scan_id = str(uuid.uuid4())

    # Create scan result object (reuse ScanResult for consistency)
    scan_result = ScanResult(
        scan_id=scan_id,
        request=None,  # Auto-discovery doesn't use ScanRequest
        status=DiscoveryStatus.PENDING
    )

    # Store scan result
    _scan_results[scan_id] = scan_result

    # Start background auto-discovery
    background_tasks.add_task(_perform_auto_discovery, scan_id, request)

    return ScanResponse(
        scan_id=scan_id,
        status=DiscoveryStatus.PENDING,
        message="Auto-discovery started successfully"
    )


async def _perform_scan(scan_id: str) -> None:
    """
    Perform the actual network scan in the background.

    Args:
        scan_id: Unique scan identifier
    """
    scan_result = _scan_results[scan_id]
    scan_result.status = DiscoveryStatus.RUNNING
    scan_result.progress = {"phase": "initializing", "percent": 0}

    try:
        # Initialize services
        scanner = NetworkScanner()
        snmp_discovery = SNMPDiscovery()
        fingerprinter = DeviceFingerprinter()

        # Phase 1: Network scanning
        scan_result.progress = {"phase": "network_scan", "percent": 10}
        devices = await scanner.scan_network(scan_result.request.network)

        # Phase 2: SNMP discovery
        scan_result.progress = {"phase": "snmp_discovery", "percent": 30}
        for device in devices:
            if scan_result.request.include_snmp:
                snmp_info = await snmp_discovery.discover_device(device.ip_address)
                if snmp_info:
                    device.snmp_info = snmp_info

        # Phase 3: Fingerprinting
        scan_result.progress = {"phase": "fingerprinting", "percent": 60}
        for device in devices:
            fingerprint = await fingerprinter.fingerprint_device(
                device.ip_address,
                device.snmp_info,
                device.ssh_info,
                device.mac_address
            )
            device.fingerprint = fingerprint

        # Phase 4: Topology discovery (if requested)
        if scan_result.request.include_lldp_cdp:
            scan_result.progress = {"phase": "topology_discovery", "percent": 80}
            topology = TopologyDiscovery()
            for device in devices:
                # Note: This would need credentials to work properly
                # For now, skip topology discovery without credentials
                pass

        # Complete scan
        scan_result.status = DiscoveryStatus.COMPLETED
        scan_result.devices = devices
        scan_result.completed_at = datetime.now(timezone.utc)
        scan_result.duration_seconds = (
            scan_result.completed_at - scan_result.started_at
        ).total_seconds()
        scan_result.progress = {"phase": "completed", "percent": 100}

    except Exception as e:
        scan_result.status = DiscoveryStatus.FAILED
        scan_result.error_message = str(e)
        scan_result.completed_at = datetime.now(timezone.utc)


async def _perform_auto_discovery(scan_id: str, request: AutoDiscoveryRequest) -> None:
    """
    Perform automatic network discovery in the background.

    Args:
        scan_id: Unique scan identifier
        request: Auto-discovery request parameters
    """
    scan_result = _scan_results[scan_id]
    scan_result.status = DiscoveryStatus.RUNNING
    scan_result.progress = {"phase": "initializing", "percent": 0}

    try:
        # Initialize services
        topology = TopologyDiscovery()
        snmp_discovery = SNMPDiscovery()
        fingerprinter = DeviceFingerprinter()

        # Phase 1: Auto-discovery from seed
        scan_result.progress = {"phase": "auto_discovery", "percent": 20}
        devices = await topology.auto_discover(
            request.seed_ip,
            request.credentials or {},
            request.max_hops
        )

        # Phase 2: Enrich with SNMP information
        scan_result.progress = {"phase": "snmp_enrichment", "percent": 60}
        for device in devices:
            snmp_info = await snmp_discovery.discover_device(device.ip_address)
            if snmp_info:
                device.snmp_info = snmp_info

        # Phase 3: Fingerprinting
        scan_result.progress = {"phase": "fingerprinting", "percent": 80}
        for device in devices:
            fingerprint = await fingerprinter.fingerprint_device(
                device.ip_address,
                device.snmp_info,
                device.ssh_info,
                device.mac_address
            )
            device.fingerprint = fingerprint

        # Complete auto-discovery
        scan_result.status = DiscoveryStatus.COMPLETED
        scan_result.devices = devices
        scan_result.completed_at = datetime.now(timezone.utc)
        scan_result.duration_seconds = (
            scan_result.completed_at - scan_result.started_at
        ).total_seconds()
        scan_result.progress = {"phase": "completed", "percent": 100}

    except Exception as e:
        scan_result.status = DiscoveryStatus.FAILED
        scan_result.error_message = str(e)
        scan_result.completed_at = datetime.now(timezone.utc)