"""
Interface model — represents a single network interface on a device.
"""
from __future__ import annotations

import ipaddress
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class InterfaceStatus(str, Enum):
    """Operational state of an interface."""

    UP = "up"
    DOWN = "down"
    ADMIN_DOWN = "admin_down"  # explicitly shut down
    UNKNOWN = "unknown"


class InterfaceType(str, Enum):
    """Logical type inferred from the interface name."""

    ETHERNET = "ethernet"
    FAST_ETHERNET = "fast_ethernet"
    GIGABIT_ETHERNET = "gigabit_ethernet"
    TEN_GIGABIT_ETHERNET = "ten_gigabit_ethernet"
    FORTY_GIGABIT_ETHERNET = "forty_gigabit_ethernet"
    HUNDRED_GIGABIT_ETHERNET = "hundred_gigabit_ethernet"
    LOOPBACK = "loopback"
    VLAN = "vlan"
    TUNNEL = "tunnel"
    MANAGEMENT = "management"
    SERIAL = "serial"
    PORT_CHANNEL = "port_channel"
    SUBINTERFACE = "subinterface"
    NULL = "null"
    UNKNOWN = "unknown"


class SwitchportMode(str, Enum):
    """Layer-2 switchport operating mode."""

    ACCESS = "access"
    TRUNK = "trunk"
    HYBRID = "hybrid"  # Huawei
    ROUTED = "routed"  # L3 port
    UNKNOWN = "unknown"


class Interface(BaseModel):
    """
    Represents a single network interface parsed from device configuration.

    Attributes:
        name: Interface name as it appears in config (e.g. "GigabitEthernet0/0").
        description: Operator-supplied description.
        interface_type: Logical type derived from the name.
        admin_status: False when the interface is administratively shut down.
        status: Last-known operational status (up/down/admin_down).
        ip_address: IPv4 or IPv6 address string (without prefix).
        subnet_mask: IPv4 subnet mask (e.g. "255.255.255.0").
        prefix_length: CIDR prefix length (derived from mask or set directly).
        secondary_ips: Additional IP addresses on the same interface.
        mtu: MTU in bytes.
        speed: Speed in Mbps.
        duplex: "full", "half", or "auto".
        switchport_mode: Layer-2 operating mode.
        access_vlan: VLAN ID when in access mode.
        trunk_vlans: Allowed VLAN list when in trunk mode.
        native_vlan: Native (untagged) VLAN on trunk ports.
        vrf: VRF the interface is associated with.
        channel_group: Port-channel group number.
    """

    name: str = Field(..., description="Interface name")
    description: Optional[str] = Field(None, description="Interface description")
    interface_type: InterfaceType = Field(
        default=InterfaceType.UNKNOWN, description="Logical interface type"
    )

    # Administrative / operational state
    admin_status: bool = Field(default=True, description="Administratively enabled")
    status: InterfaceStatus = Field(
        default=InterfaceStatus.UNKNOWN, description="Operational status"
    )

    # Addressing
    ip_address: Optional[str] = Field(None, description="Primary IPv4/IPv6 address")
    subnet_mask: Optional[str] = Field(None, description="IPv4 subnet mask")
    prefix_length: Optional[int] = Field(None, ge=0, le=128, description="CIDR prefix length")
    secondary_ips: list[str] = Field(
        default_factory=list, description="Secondary IP addresses"
    )

    # Physical characteristics
    mtu: Optional[int] = Field(None, ge=64, le=65535, description="MTU in bytes")
    speed: Optional[int] = Field(None, ge=0, description="Speed in Mbps")
    duplex: Optional[str] = Field(None, description="Duplex: full / half / auto")

    # Layer-2
    switchport_mode: SwitchportMode = Field(
        default=SwitchportMode.ROUTED, description="Switchport mode"
    )
    access_vlan: Optional[int] = Field(None, ge=1, le=4094, description="Access VLAN ID")
    trunk_vlans: list[int] = Field(
        default_factory=list, description="Trunk allowed VLAN IDs"
    )
    native_vlan: Optional[int] = Field(None, ge=1, le=4094, description="Native VLAN ID")

    # Misc
    vrf: Optional[str] = Field(None, description="Associated VRF name")
    channel_group: Optional[int] = Field(None, description="Port-channel group number")

    @model_validator(mode="after")
    def derive_prefix_length(self) -> "Interface":
        """
        Derive prefix_length from subnet_mask when prefix_length is not set,
        and ensure the status reflects admin_status.
        """
        if self.subnet_mask and self.prefix_length is None:
            try:
                network = ipaddress.IPv4Network(
                    f"0.0.0.0/{self.subnet_mask}", strict=False
                )
                object.__setattr__(self, "prefix_length", network.prefixlen)
            except ValueError:
                pass  # keep prefix_length as None

        if not self.admin_status and self.status == InterfaceStatus.UNKNOWN:
            object.__setattr__(self, "status", InterfaceStatus.ADMIN_DOWN)

        return self

    @property
    def cidr_notation(self) -> Optional[str]:
        """
        Return the interface address in CIDR notation (e.g. "192.168.1.1/24"),
        or None when no IP is configured.
        """
        if self.ip_address and self.prefix_length is not None:
            return f"{self.ip_address}/{self.prefix_length}"
        return None

    @property
    def is_layer3(self) -> bool:
        """True when a routable IP address is configured."""
        return self.ip_address is not None

    @property
    def is_loopback(self) -> bool:
        """True for loopback interfaces."""
        return self.interface_type == InterfaceType.LOOPBACK

    def __str__(self) -> str:
        return f"Interface({self.name}, {self.status.value})"


def detect_interface_type(name: str) -> InterfaceType:
    """
    Infer the InterfaceType from an interface name string.

    Args:
        name: Interface name as it appears in configuration.

    Returns:
        Best-matching InterfaceType enum value.
    """
    name_lower = name.lower()

    if name_lower.startswith("lo"):
        return InterfaceType.LOOPBACK
    if name_lower.startswith("tunnel"):
        return InterfaceType.TUNNEL
    if name_lower.startswith("vlan") or name_lower.startswith("irb"):
        return InterfaceType.VLAN
    if name_lower.startswith("mgmt") or name_lower.startswith("management"):
        return InterfaceType.MANAGEMENT
    if name_lower.startswith("port-channel") or name_lower.startswith("po"):
        return InterfaceType.PORT_CHANNEL
    if name_lower.startswith("serial"):
        return InterfaceType.SERIAL
    if name_lower.startswith("null"):
        return InterfaceType.NULL
    if name_lower.startswith("hundredgige") or name_lower.startswith("hu"):
        return InterfaceType.HUNDRED_GIGABIT_ETHERNET
    if name_lower.startswith("fortygige") or name_lower.startswith("fo"):
        return InterfaceType.FORTY_GIGABIT_ETHERNET
    if name_lower.startswith("tengige") or name_lower.startswith("te"):
        return InterfaceType.TEN_GIGABIT_ETHERNET
    if name_lower.startswith("gigabitethernet") or name_lower.startswith("gi"):
        return InterfaceType.GIGABIT_ETHERNET
    if name_lower.startswith("fastethernet") or name_lower.startswith("fa"):
        return InterfaceType.FAST_ETHERNET
    if name_lower.startswith("ethernet") or name_lower.startswith("eth"):
        return InterfaceType.ETHERNET
    if "." in name:
        return InterfaceType.SUBINTERFACE

    return InterfaceType.UNKNOWN
