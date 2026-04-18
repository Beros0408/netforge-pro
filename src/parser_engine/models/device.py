"""
Device model — top-level representation of a parsed network device.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .interface import Interface
from .vlan import VLAN
from .routing import Route, OSPFProcess, BGPProcess, VRF
from .security import ACL, FirewallPolicy, NATRule


class OSType(str, Enum):
    """Operating system type for a parsed device."""

    VRP = "vrp"
    IOS = "ios"
    IOS_XE = "ios_xe"
    NXOS = "nxos"
    EOS = "eos"
    FORTIOS = "fortios"
    UNKNOWN = "unknown"


class VendorType(str, Enum):
    """Supported network OS / vendor identifiers."""

    CISCO = "cisco"
    FORTINET = "fortinet"
    HUAWEI = "huawei"
    ARISTA = "arista"

    CISCO_IOS = "cisco"
    CISCO_NXOS = "cisco"
    CISCO_IOSXE = "cisco"
    CISCO_IOSXR = "cisco"
    FORTINET_FORTIOS = "fortinet"
    HUAWEI_VRP = "huawei"
    ARISTA_EOS = "arista"
    UNKNOWN = "unknown"


class Device(BaseModel):
    """
    Complete representation of a parsed network device configuration.

    Attributes:
        hostname: Device hostname as configured.
        vendor: Detected or specified vendor / OS type.
        os_version: Operating system version string.
        model: Hardware model (e.g. "Catalyst 9300").
        serial_number: Chassis serial number.
        interfaces: List of parsed interfaces.
        vlans: List of parsed VLANs.
        static_routes: List of static routes.
        ospf_processes: List of OSPF routing processes.
        bgp_processes: List of BGP routing processes.
        acls: List of access control lists.
        firewall_policies: List of firewall policies (FortiOS/ASA).
        nat_rules: List of NAT rules.
        raw_config: Original configuration text.
        parsed_at: UTC timestamp of parsing.
    """

    hostname: str = Field(..., description="Device hostname")
    vendor: VendorType = Field(..., description="Vendor / OS type")
    os_version: Optional[str] = Field(None, description="OS version string")
    os_type: Optional[OSType] = Field(None, description="Operating system type")
    model: Optional[str] = Field(None, description="Hardware model")
    serial_number: Optional[str] = Field(None, description="Chassis serial number")

    # Network constructs
    interfaces: list[Interface] = Field(default_factory=list, description="Parsed interfaces")
    vlans: list[VLAN] = Field(default_factory=list, description="Parsed VLANs")
    static_routes: list[Route] = Field(default_factory=list, description="Static routes")
    ospf_processes: list[OSPFProcess] = Field(
        default_factory=list, description="OSPF routing processes"
    )
    bgp_processes: list[BGPProcess] = Field(
        default_factory=list, description="BGP routing processes"
    )
    vrfs: list[VRF] = Field(default_factory=list, description="VRF definitions")

    # VXLAN constructs
    vxlan_vni_mappings: dict[int, int] = Field(default_factory=dict, description="VXLAN VNI mappings {vlan_id: vni}")

    # Security constructs
    acls: list[ACL] = Field(default_factory=list, description="Access control lists")
    firewall_policies: list[FirewallPolicy] = Field(
        default_factory=list, description="Firewall policies"
    )
    nat_rules: list[NATRule] = Field(default_factory=list, description="NAT rules")

    # Meta
    raw_config: str = Field(default="", description="Original raw configuration text")
    parsed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of parsing",
    )

    @field_validator("hostname")
    @classmethod
    def hostname_not_empty(cls, v: str) -> str:
        """Ensure hostname is not an empty string."""
        if not v.strip():
            raise ValueError("hostname must not be empty")
        return v.strip()

    def get_interface(self, name: str) -> Optional[Interface]:
        """
        Look up an interface by name (case-insensitive).

        Args:
            name: Interface name, e.g. "GigabitEthernet0/0".

        Returns:
            Matching Interface or None.
        """
        name_lower = name.lower()
        for iface in self.interfaces:
            if iface.name.lower() == name_lower:
                return iface
        return None

    def get_vlan(self, vlan_id: int) -> Optional[VLAN]:
        """
        Look up a VLAN by its numeric ID.

        Args:
            vlan_id: VLAN identifier (1-4094).

        Returns:
            Matching VLAN or None.
        """
        for vlan in self.vlans:
            if vlan.vlan_id == vlan_id:
                return vlan
        return None

    @property
    def interface_count(self) -> int:
        """Total number of parsed interfaces."""
        return len(self.interfaces)

    @property
    def active_interface_count(self) -> int:
        """Number of interfaces that are administratively up."""
        from .interface import InterfaceStatus
        return sum(
            1 for iface in self.interfaces
            if iface.admin_status and iface.status != InterfaceStatus.ADMIN_DOWN
        )

    model_config = {"use_enum_values": False}


class ParsedDevice(BaseModel):
    """
    Lightweight wrapper returned by the parsing service,
    including parsing metadata alongside the device object.
    """

    device: Device = Field(..., description="Parsed device data")
    parser_version: str = Field(..., description="Parser version used")
    parsing_duration_ms: float = Field(..., description="Parsing duration in milliseconds")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal parsing warnings")
    errors: list[str] = Field(default_factory=list, description="Fatal parsing errors (empty = success)")

    @property
    def success(self) -> bool:
        """True when no fatal parsing errors were recorded."""
        return len(self.errors) == 0
