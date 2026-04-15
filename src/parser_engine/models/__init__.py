"""
Parser Engine data models.
"""
from .device import Device, VendorType, ParsedDevice
from .interface import Interface, InterfaceStatus, InterfaceType
from .vlan import VLAN
from .routing import Route, RouteProtocol, OSPFProcess, OSPFNetwork, BGPProcess, BGPNeighbor
from .security import ACL, ACLEntry, ACLType, FirewallPolicy, FirewallPolicyAction, NATRule

__all__ = [
    "Device",
    "VendorType",
    "ParsedDevice",
    "Interface",
    "InterfaceStatus",
    "InterfaceType",
    "VLAN",
    "Route",
    "RouteProtocol",
    "OSPFProcess",
    "OSPFNetwork",
    "BGPProcess",
    "BGPNeighbor",
    "ACL",
    "ACLEntry",
    "ACLType",
    "FirewallPolicy",
    "FirewallPolicyAction",
    "NATRule",
]
