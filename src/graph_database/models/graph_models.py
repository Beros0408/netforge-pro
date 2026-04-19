"""
Graph models for Neo4j nodes and relationships.
Pydantic models representing the graph structure for network infrastructure.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Neo4j node labels."""
    DEVICE = "Device"
    INTERFACE = "Interface"
    VLAN = "VLAN"
    VRF = "VRF"
    ZONE = "Zone"


class RelationshipType(str, Enum):
    """Neo4j relationship types."""
    CONNECTED_TO = "CONNECTED_TO"
    HAS_INTERFACE = "HAS_INTERFACE"
    MEMBER_OF_VLAN = "MEMBER_OF_VLAN"
    ROUTES_TO = "ROUTES_TO"
    LOCATED_IN = "LOCATED_IN"


# ============================================================================
# NODE MODELS
# ============================================================================

class DeviceNode(BaseModel):
    """
    Device node in the graph database.

    Represents a network device with its properties.
    """
    # Neo4j internal ID (set by database)
    node_id: Optional[int] = Field(None, description="Neo4j internal node ID")

    # Core properties
    hostname: str = Field(..., description="Device hostname")
    vendor: str = Field(..., description="Device vendor (cisco, huawei, etc.)")
    model: Optional[str] = Field(None, description="Hardware model")
    os_version: Optional[str] = Field(None, description="Operating system version")
    zone: Optional[str] = Field(None, description="Network zone/location")

    # Additional metadata
    serial_number: Optional[str] = Field(None, description="Chassis serial number")
    management_ip: Optional[str] = Field(None, description="Management IP address")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Labels for Neo4j
    labels: list[str] = Field(default_factory=lambda: [NodeType.DEVICE.value], description="Neo4j node labels")

    def __str__(self) -> str:
        return f"Device({self.hostname}, {self.vendor})"


class InterfaceNode(BaseModel):
    """
    Interface node in the graph database.

    Represents a network interface on a device.
    """
    # Neo4j internal ID
    node_id: Optional[int] = Field(None, description="Neo4j internal node ID")

    # Core properties
    name: str = Field(..., description="Interface name (e.g., GigabitEthernet0/0)")
    interface_type: str = Field(..., description="Interface type (ethernet, vlan, etc.)")
    ip_address: Optional[str] = Field(None, description="Primary IP address")
    vlan: Optional[int] = Field(None, description="Access VLAN ID")
    state: str = Field(default="unknown", description="Interface state (up/down)")

    # Physical properties
    speed: Optional[int] = Field(None, description="Speed in Mbps")
    duplex: Optional[str] = Field(None, description="Duplex mode (full/half/auto)")
    mtu: Optional[int] = Field(None, description="MTU size")

    # Additional metadata
    description: Optional[str] = Field(None, description="Interface description")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Labels for Neo4j
    labels: list[str] = Field(default_factory=lambda: [NodeType.INTERFACE.value], description="Neo4j node labels")

    def __str__(self) -> str:
        return f"Interface({self.name}, {self.ip_address or 'no-ip'})"


class VLANNode(BaseModel):
    """
    VLAN node in the graph database.

    Represents a VLAN configuration.
    """
    # Neo4j internal ID
    node_id: Optional[int] = Field(None, description="Neo4j internal node ID")

    # Core properties
    vlan_id: int = Field(..., ge=1, le=4094, description="VLAN ID")
    name: Optional[str] = Field(None, description="VLAN name")
    svi_ip: Optional[str] = Field(None, description="SVI IP address")

    # Additional metadata
    description: Optional[str] = Field(None, description="VLAN description")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Labels for Neo4j
    labels: list[str] = Field(default_factory=lambda: [NodeType.VLAN.value], description="Neo4j node labels")

    def __str__(self) -> str:
        name_part = f" ({self.name})" if self.name else ""
        return f"VLAN({self.vlan_id}{name_part})"


class VRFNode(BaseModel):
    """
    VRF node in the graph database.

    Represents a VPN Routing and Forwarding instance.
    """
    # Neo4j internal ID
    node_id: Optional[int] = Field(None, description="Neo4j internal node ID")

    # Core properties
    name: str = Field(..., description="VRF name")
    rd: Optional[str] = Field(None, description="Route distinguisher")
    rt_import: list[str] = Field(default_factory=list, description="Import route targets")
    rt_export: list[str] = Field(default_factory=list, description="Export route targets")

    # Additional metadata
    description: Optional[str] = Field(None, description="VRF description")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Labels for Neo4j
    labels: list[str] = Field(default_factory=lambda: [NodeType.VRF.value], description="Neo4j node labels")

    def __str__(self) -> str:
        return f"VRF({self.name})"


class ZoneNode(BaseModel):
    """
    Zone node in the graph database.

    Represents a network zone or segment.
    """
    # Neo4j internal ID
    node_id: Optional[int] = Field(None, description="Neo4j internal node ID")

    # Core properties
    name: str = Field(..., description="Zone name")
    zone_type: str = Field(default="network", description="Zone type (network, security, etc.)")
    security_level: int = Field(default=0, ge=0, le=100, description="Security level (0-100)")

    # Additional metadata
    description: Optional[str] = Field(None, description="Zone description")
    color: Optional[str] = Field(None, description="Display color for visualization")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Labels for Neo4j
    labels: list[str] = Field(default_factory=lambda: [NodeType.ZONE.value], description="Neo4j node labels")

    def __str__(self) -> str:
        return f"Zone({self.name}, level={self.security_level})"


# ============================================================================
# RELATIONSHIP MODELS
# ============================================================================

class BaseRelationship(BaseModel):
    """
    Base class for all relationship models.
    """
    # Neo4j internal ID
    rel_id: Optional[int] = Field(None, description="Neo4j internal relationship ID")

    # Relationship metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class ConnectedTo(BaseRelationship):
    """
    CONNECTED_TO relationship between interfaces.

    Represents physical or logical connections between network interfaces.
    """
    # Relationship properties
    cable_type: Optional[str] = Field(None, description="Cable type (fiber, copper, etc.)")
    speed: Optional[int] = Field(None, description="Connection speed in Mbps")
    bandwidth: Optional[int] = Field(None, description="Allocated bandwidth in Mbps")
    status: str = Field(default="active", description="Connection status")

    # Neo4j relationship type
    type: str = Field(default=RelationshipType.CONNECTED_TO.value, description="Relationship type")

    def __str__(self) -> str:
        return f"CONNECTED_TO(speed={self.speed}Mbps)"


class HasInterface(BaseRelationship):
    """
    HAS_INTERFACE relationship between Device and Interface.

    Represents that a device contains an interface.
    """
    # Relationship properties
    interface_role: Optional[str] = Field(None, description="Interface role (management, data, etc.)")

    # Neo4j relationship type
    type: str = Field(default=RelationshipType.HAS_INTERFACE.value, description="Relationship type")

    def __str__(self) -> str:
        return "HAS_INTERFACE"


class MemberOfVLAN(BaseRelationship):
    """
    MEMBER_OF_VLAN relationship between Interface and VLAN.

    Represents VLAN membership of an interface.
    """
    # Relationship properties
    mode: str = Field(default="access", description="VLAN mode (access/trunk)")
    native: bool = Field(default=False, description="Native VLAN on trunk")
    allowed_vlans: list[int] = Field(default_factory=list, description="Allowed VLANs on trunk")

    # Neo4j relationship type
    type: str = Field(default=RelationshipType.MEMBER_OF_VLAN.value, description="Relationship type")

    def __str__(self) -> str:
        if self.mode == "trunk":
            return f"MEMBER_OF_VLAN(trunk, native={self.native})"
        return f"MEMBER_OF_VLAN(access)"


class RoutesTo(BaseRelationship):
    """
    ROUTES_TO relationship between Devices.

    Represents routing relationships between devices.
    """
    # Relationship properties
    protocol: str = Field(default="static", description="Routing protocol")
    metric: Optional[int] = Field(None, description="Route metric")
    next_hop: Optional[str] = Field(None, description="Next hop IP")
    network: Optional[str] = Field(None, description="Destination network")

    # Neo4j relationship type
    type: str = Field(default=RelationshipType.ROUTES_TO.value, description="Relationship type")

    def __str__(self) -> str:
        return f"ROUTES_TO({self.protocol}, metric={self.metric})"


class LocatedIn(BaseRelationship):
    """
    LOCATED_IN relationship between Device and Zone.

    Represents device placement in network zones.
    """
    # Relationship properties
    role: Optional[str] = Field(None, description="Device role in zone (gateway, host, etc.)")

    # Neo4j relationship type
    type: str = Field(default=RelationshipType.LOCATED_IN.value, description="Relationship type")

    def __str__(self) -> str:
        return "LOCATED_IN"