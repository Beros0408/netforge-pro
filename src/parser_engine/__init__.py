"""
Parser Engine - Module 1
========================
Parses network device configurations from multiple vendors
(Cisco IOS, Cisco NX-OS, FortiOS, Huawei VRP, Arista EOS).

Exports the main public surface of the module.
"""

from .config import settings as parser_settings
from .models.device import Device, VendorType
from .models.interface import Interface, InterfaceStatus, InterfaceType
from .models.vlan import VLAN
from .models.routing import Route, RouteProtocol, OSPFProcess, BGPProcess
from .models.security import ACL, FirewallPolicy
from .services.parsing_service import ParsingService

__all__ = [
    "parser_settings",
    "Device",
    "VendorType",
    "Interface",
    "InterfaceStatus",
    "InterfaceType",
    "VLAN",
    "Route",
    "RouteProtocol",
    "OSPFProcess",
    "BGPProcess",
    "ACL",
    "FirewallPolicy",
    "ParsingService",
]

__version__ = "1.0.0"
