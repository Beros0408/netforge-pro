"""
Graph models for Neo4j nodes and relationships.
"""
from .graph_models import (
    DeviceNode,
    InterfaceNode,
    VLANNode,
    VRFNode,
    ZoneNode,
    ConnectedTo,
    HasInterface,
    MemberOfVLAN,
    RoutesTo,
    LocatedIn,
)

__all__ = [
    "DeviceNode",
    "InterfaceNode",
    "VLANNode",
    "VRFNode",
    "ZoneNode",
    "ConnectedTo",
    "HasInterface",
    "MemberOfVLAN",
    "RoutesTo",
    "LocatedIn",
]