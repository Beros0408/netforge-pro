"""
Routing models — static routes, OSPF, BGP.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RouteProtocol(str, Enum):
    """Origin protocol of a routing table entry."""

    STATIC = "static"
    CONNECTED = "connected"
    LOCAL = "local"
    OSPF = "ospf"
    OSPF_E1 = "ospf_e1"
    OSPF_E2 = "ospf_e2"
    BGP = "bgp"
    BGP_EXTERNAL = "ebgp"
    RIP = "rip"
    EIGRP = "eigrp"
    ISIS = "isis"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Static / generic routes
# ---------------------------------------------------------------------------

class Route(BaseModel):
    """
    A single routing table entry (static or redistributed).

    Attributes:
        network: Destination network address.
        prefix_length: CIDR prefix length.
        subnet_mask: IPv4 dotted-decimal mask (alternative to prefix_length).
        next_hop: Next-hop IP address.
        exit_interface: Outgoing interface name.
        metric: Route metric / cost.
        admin_distance: Administrative distance.
        protocol: Origin protocol.
        vrf: VRF the route belongs to.
        tag: Optional route tag.
        description: Operator description.
    """

    network: str = Field(..., description="Destination network")
    prefix_length: Optional[int] = Field(None, ge=0, le=128, description="CIDR prefix length")
    subnet_mask: Optional[str] = Field(None, description="IPv4 subnet mask")
    next_hop: Optional[str] = Field(None, description="Next-hop IP address")
    exit_interface: Optional[str] = Field(None, description="Outgoing interface name")
    metric: Optional[int] = Field(None, ge=0, description="Route metric")
    admin_distance: Optional[int] = Field(None, ge=0, le=255, description="Admin distance")
    protocol: RouteProtocol = Field(default=RouteProtocol.STATIC, description="Origin protocol")
    vrf: Optional[str] = Field(None, description="VRF name")
    tag: Optional[int] = Field(None, description="Route tag")
    description: Optional[str] = Field(None, description="Route description")

    def __str__(self) -> str:
        dest = (
            f"{self.network}/{self.prefix_length}"
            if self.prefix_length is not None
            else self.network
        )
        via = self.next_hop or self.exit_interface or "?"
        return f"Route({self.protocol.value}) {dest} via {via}"


# ---------------------------------------------------------------------------
# OSPF
# ---------------------------------------------------------------------------

class OSPFNetwork(BaseModel):
    """
    A network statement within an OSPF process.

    Attributes:
        network: Network address.
        wildcard: Wildcard mask (Cisco-style).
        area: OSPF area identifier (numeric or dotted-decimal).
    """

    network: str = Field(..., description="Network address")
    wildcard: Optional[str] = Field(None, description="Wildcard mask")
    area: str = Field(..., description="OSPF area (e.g. '0' or '0.0.0.0')")


class OSPFRedistribution(BaseModel):
    """Redistribution entry inside an OSPF process."""

    source_protocol: str = Field(..., description="Protocol being redistributed")
    metric: Optional[int] = Field(None, description="Redistribution metric")
    metric_type: Optional[int] = Field(None, ge=1, le=2, description="External metric type (1 or 2)")
    subnets: bool = Field(default=True, description="Include subnets")
    route_map: Optional[str] = Field(None, description="Route-map applied during redistribution")


class OSPFProcess(BaseModel):
    """
    An OSPF routing process.

    Attributes:
        process_id: OSPF process identifier.
        router_id: Configured or elected router-ID.
        networks: List of network statements.
        passive_interfaces: Interfaces configured as passive.
        redistributions: Redistribution rules.
        vrf: VRF this process runs in.
    """

    process_id: int = Field(..., ge=1, description="OSPF process ID")
    router_id: Optional[str] = Field(None, description="Router-ID")
    networks: list[OSPFNetwork] = Field(default_factory=list)
    passive_interfaces: list[str] = Field(
        default_factory=list, description="Passive interface names"
    )
    redistributions: list[OSPFRedistribution] = Field(default_factory=list)
    vrf: Optional[str] = Field(None, description="VRF name")


# ---------------------------------------------------------------------------
# BGP
# ---------------------------------------------------------------------------

class BGPNeighbor(BaseModel):
    """
    A single BGP peer (neighbor).

    Attributes:
        address: Peer IP address.
        remote_as: Remote autonomous system number.
        description: Peer description.
        update_source: Source interface for BGP updates.
        next_hop_self: Whether next-hop-self is configured.
        route_map_in: Inbound route-map name.
        route_map_out: Outbound route-map name.
        password: MD5 authentication password (redacted in logs).
        shutdown: Whether the neighbor is administratively shut down.
    """

    address: str = Field(..., description="Peer IP address")
    remote_as: int = Field(..., ge=1, description="Remote AS number")
    description: Optional[str] = Field(None, description="Peer description")
    update_source: Optional[str] = Field(None, description="Source interface")
    next_hop_self: bool = Field(default=False)
    route_map_in: Optional[str] = Field(None, description="Inbound route-map")
    route_map_out: Optional[str] = Field(None, description="Outbound route-map")
    password: Optional[str] = Field(None, description="MD5 password (masked)")
    shutdown: bool = Field(default=False)


class BGPNetwork(BaseModel):
    """A network advertised via BGP."""

    network: str = Field(..., description="Network address")
    mask: Optional[str] = Field(None, description="Subnet mask")
    route_map: Optional[str] = Field(None, description="Route-map applied")


class BGPProcess(BaseModel):
    """
    A BGP routing process.

    Attributes:
        local_as: Local autonomous system number.
        router_id: BGP router-ID.
        neighbors: List of BGP neighbors.
        networks: Networks originated by this BGP process.
        vrf: VRF this process runs in.
    """

    local_as: int = Field(..., ge=1, description="Local AS number")
    router_id: Optional[str] = Field(None, description="BGP router-ID")
    neighbors: list[BGPNeighbor] = Field(default_factory=list)
    networks: list[BGPNetwork] = Field(default_factory=list)
    vrf: Optional[str] = Field(None, description="VRF name")
