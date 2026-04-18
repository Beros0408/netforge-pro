"""
Discovery Engine models for network device discovery.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from ipaddress import IPv4Address, IPv4Network

from pydantic import BaseModel, Field, field_validator


class DiscoveryStatus(str, Enum):
    """Status of a discovery operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PortStatus(str, Enum):
    """Status of a network port."""

    OPEN = "open"
    CLOSED = "closed"
    FILTERED = "filtered"
    UNKNOWN = "unknown"


class VendorType(str, Enum):
    """Supported network device vendors."""

    CISCO = "cisco"
    HUAWEI = "huawei"
    ARISTA = "arista"
    FORTINET = "fortinet"
    JUNIPER = "juniper"
    EXTREME = "extreme"
    BROCADE = "brocade"
    HP = "hp"
    DELL = "dell"
    UNKNOWN = "unknown"


class DeviceType(str, Enum):
    """Type of network device."""

    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    ACCESS_POINT = "access_point"
    SERVER = "server"
    UNKNOWN = "unknown"


class PortInfo(BaseModel):
    """Information about a network port."""

    port: int = Field(..., description="Port number")
    status: PortStatus = Field(..., description="Port status")
    service: Optional[str] = Field(None, description="Service name if known")
    banner: Optional[str] = Field(None, description="Service banner if available")


class SNMPInfo(BaseModel):
    """SNMP information from a device."""

    sysDescr: Optional[str] = Field(None, description="System description (SNMP OID 1.3.6.1.2.1.1.1)")
    sysName: Optional[str] = Field(None, description="System name (SNMP OID 1.3.6.1.2.1.1.5)")
    sysLocation: Optional[str] = Field(None, description="System location (SNMP OID 1.3.6.1.2.1.1.6)")
    sysContact: Optional[str] = Field(None, description="System contact (SNMP OID 1.3.6.1.2.1.1.4)")
    sysUpTime: Optional[str] = Field(None, description="System uptime")
    ifNumber: Optional[int] = Field(None, description="Number of interfaces")


class SSHInfo(BaseModel):
    """SSH information from a device."""

    banner: Optional[str] = Field(None, description="SSH banner")
    version: Optional[str] = Field(None, description="SSH version")
    key_fingerprint: Optional[str] = Field(None, description="SSH key fingerprint")


class MACInfo(BaseModel):
    """MAC address information."""

    address: str = Field(..., description="MAC address")
    oui: Optional[str] = Field(None, description="Organizationally Unique Identifier")
    vendor: Optional[str] = Field(None, description="Vendor name from OUI")


class FingerprintResult(BaseModel):
    """Result of device fingerprinting."""

    vendor: VendorType = Field(..., description="Detected vendor")
    device_type: DeviceType = Field(..., description="Detected device type")
    os_version: Optional[str] = Field(None, description="Operating system version")
    model: Optional[str] = Field(None, description="Device model")
    confidence_score: float = Field(..., description="Confidence score (0.0 to 1.0)")
    fingerprint_sources: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores by source (snmp, ssh, mac)"
    )
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When fingerprinting was performed"
    )


class NeighborInfo(BaseModel):
    """Information about a network neighbor (LLDP/CDP)."""

    local_interface: str = Field(..., description="Local interface name")
    remote_device: str = Field(..., description="Remote device hostname/IP")
    remote_interface: str = Field(..., description="Remote interface name")
    remote_vendor: Optional[VendorType] = Field(None, description="Remote device vendor")
    protocol: str = Field(..., description="Discovery protocol (LLDP/CDP)")
    capabilities: List[str] = Field(default_factory=list, description="Device capabilities")


class DiscoveredDevice(BaseModel):
    """Complete information about a discovered network device."""

    ip_address: IPv4Address = Field(..., description="Device IP address")
    hostname: Optional[str] = Field(None, description="Device hostname")
    mac_address: Optional[MACInfo] = Field(None, description="MAC address information")

    # Discovery results
    is_alive: bool = Field(..., description="Whether device responds to ping")
    open_ports: List[PortInfo] = Field(default_factory=list, description="Open ports found")
    snmp_info: Optional[SNMPInfo] = Field(None, description="SNMP information")
    ssh_info: Optional[SSHInfo] = Field(None, description="SSH information")

    # Fingerprinting results
    fingerprint: Optional[FingerprintResult] = Field(None, description="Device fingerprint")

    # Network topology
    neighbors: List[NeighborInfo] = Field(default_factory=list, description="Network neighbors")

    # Metadata
    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When device was discovered"
    )
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When device was last seen"
    )
    discovery_method: str = Field(..., description="How device was discovered")
    tags: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('ip_address', mode='before')
    @classmethod
    def validate_ip_address(cls, v):
        """Convert string IP to IPv4Address."""
        if isinstance(v, str):
            return IPv4Address(v)
        return v


class ScanRequest(BaseModel):
    """Request to perform a network scan."""

    network: IPv4Network = Field(..., description="Network range to scan (CIDR notation)")
    ports: Optional[List[int]] = Field(None, description="Specific ports to scan")
    include_snmp: bool = Field(True, description="Include SNMP discovery")
    include_ssh: bool = Field(True, description="Include SSH banner detection")
    include_lldp_cdp: bool = Field(True, description="Include LLDP/CDP neighbor discovery")
    max_hosts: Optional[int] = Field(None, description="Maximum number of hosts to scan")
    timeout: Optional[int] = Field(None, description="Scan timeout in seconds")

    @field_validator('network', mode='before')
    @classmethod
    def validate_network(cls, v):
        """Convert string network to IPv4Network."""
        if isinstance(v, str):
            return IPv4Network(v)
        return v


class ScanResult(BaseModel):
    """Result of a network scan operation."""

    scan_id: str = Field(..., description="Unique scan identifier")
    request: ScanRequest = Field(..., description="Original scan request")
    status: DiscoveryStatus = Field(..., description="Scan status")
    devices: List[DiscoveredDevice] = Field(default_factory=list, description="Discovered devices")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When scan started"
    )
    completed_at: Optional[datetime] = Field(None, description="When scan completed")
    duration_seconds: Optional[float] = Field(None, description="Scan duration")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    progress: Dict[str, Any] = Field(default_factory=dict, description="Scan progress information")


class AutoDiscoveryRequest(BaseModel):
    """Request for automatic network discovery from a seed device."""

    seed_ip: IPv4Address = Field(..., description="IP address of seed device")
    max_hops: int = Field(3, description="Maximum discovery hops")
    credentials: Optional[Dict[str, Any]] = Field(None, description="SSH/SNMP credentials")
    include_neighbors: bool = Field(True, description="Include neighbor discovery")

    @field_validator('seed_ip', mode='before')
    @classmethod
    def validate_seed_ip(cls, v):
        """Convert string IP to IPv4Address."""
        if isinstance(v, str):
            return IPv4Address(v)
        return v