"""
Unit tests for the Cisco IOS parser.

Tests are grouped by feature:
  - Vendor detection (can_parse)
  - Hostname / version extraction
  - Interface parsing (L2 and L3)
  - VLAN parsing
  - Static routes
  - OSPF parsing
  - BGP parsing
  - ACL parsing
  - NAT rule parsing
  - Error / edge cases
"""
from __future__ import annotations

import pytest

from ..models.device import VendorType
from ..models.interface import InterfaceStatus, InterfaceType, SwitchportMode
from ..models.routing import RouteProtocol
from ..models.security import ACLType, ACLAction, FirewallPolicyAction, NATType
from ..parsers.cisco.ios_parser import CiscoIOSParser
from ..parsers.base_parser import ParserError

# ---------------------------------------------------------------------------
# Fixtures — minimal and realistic configs
# ---------------------------------------------------------------------------

MINIMAL_IOS_CONFIG = """\
Building configuration...

Current configuration : 1024 bytes
!
version 15.2
!
hostname ROUTER-01
!
interface GigabitEthernet0/0
 description WAN Link
 ip address 203.0.113.1 255.255.255.0
 duplex full
 speed 1000
!
interface GigabitEthernet0/1
 description LAN
 ip address 192.168.1.1 255.255.255.0
!
interface Loopback0
 ip address 10.0.0.1 255.255.255.255
!
interface GigabitEthernet0/2
 shutdown
!
end
"""

FULL_IOS_CONFIG = """\
Building configuration...
!
version 16.9
!
hostname CORE-SW-01
!
vlan 10
 name SERVERS
!
vlan 20
 name CLIENTS
 state suspend
!
interface GigabitEthernet1/0/1
 description Uplink to WAN
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30-32
 switchport trunk native vlan 99
!
interface GigabitEthernet1/0/2
 description Server VLAN
 switchport mode access
 switchport access vlan 10
!
interface Vlan10
 description Server Gateway
 ip address 10.10.10.1 255.255.255.0
 mtu 9000
!
interface Vlan20
 description Client Gateway
 ip address 10.20.20.1 255.255.255.0
 shutdown
!
ip route 0.0.0.0 0.0.0.0 203.0.113.254
ip route 192.168.100.0 255.255.255.0 10.10.10.254 100
ip route vrf MGMT 172.16.0.0 255.255.0.0 172.16.0.1
!
router ospf 1
 router-id 1.1.1.1
 network 10.10.10.0 0.0.0.255 area 0
 network 10.20.20.0 0.0.0.255 area 0
 passive-interface GigabitEthernet1/0/2
 redistribute static metric 20 metric-type 2
!
router bgp 65001
 bgp router-id 1.1.1.1
 network 10.0.0.0 mask 255.0.0.0
 neighbor 203.0.113.254 remote-as 65002
 neighbor 203.0.113.254 description ISP-Peer
 neighbor 203.0.113.254 next-hop-self
 neighbor 203.0.113.254 route-map RM-IN in
 neighbor 203.0.113.254 route-map RM-OUT out
!
ip access-list extended PERMIT-WEB
 10 permit tcp any any eq 80
 20 permit tcp any any eq 443
 30 deny ip any any
!
ip access-list standard MGMT-ACCESS
 permit 10.10.10.0 0.0.0.255
 deny any
!
access-list 10 permit 192.168.1.0 0.0.0.255
!
ip nat inside source static 192.168.1.10 203.0.113.10
ip nat inside source list 1 interface GigabitEthernet0/0 overload
!
end
"""

FORTIOS_CONFIG = """\
#config-version=FGT100D-v5.6.12-build1653:opmode=1:vdom=0
config system global
    set hostname FortiGate-01
    set alias "Branch FW"
end
config system interface
    edit "port1"
        set ip 192.168.1.1 255.255.255.0
        set alias "LAN"
        set status up
    next
    edit "port2"
        set ip 203.0.113.1 255.255.255.252
        set alias "WAN"
        set status up
    next
    edit "port3"
        set status down
    next
end
config router static
    edit 1
        set dst 0.0.0.0 0.0.0.0
        set gateway 203.0.113.2
        set device "port2"
    next
end
config firewall policy
    edit 1
        set name "LAN-to-WAN"
        set srcintf "port1"
        set dstintf "port2"
        set srcaddr "all"
        set dstaddr "all"
        set action accept
        set service "ALL"
        set nat enable
        set logtraffic all
        set status enable
    next
    edit 2
        set name "DENY-ALL"
        set srcintf "any"
        set dstintf "any"
        set srcaddr "all"
        set dstaddr "all"
        set action deny
        set logtraffic utm
        set status enable
    next
end
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def ios_parser() -> CiscoIOSParser:
    return CiscoIOSParser()


# ---------------------------------------------------------------------------
# 1. Vendor detection
# ---------------------------------------------------------------------------

class TestCanParse:
    def test_detects_building_configuration(self, ios_parser: CiscoIOSParser) -> None:
        assert ios_parser.can_parse(MINIMAL_IOS_CONFIG) is True

    def test_detects_current_configuration(self, ios_parser: CiscoIOSParser) -> None:
        config = "Current configuration : 512 bytes\nhostname R1\n"
        assert ios_parser.can_parse(config) is True

    def test_rejects_fortios(self, ios_parser: CiscoIOSParser) -> None:
        assert ios_parser.can_parse(FORTIOS_CONFIG) is False

    def test_rejects_empty_string(self, ios_parser: CiscoIOSParser) -> None:
        assert ios_parser.can_parse("") is False

    def test_rejects_random_text(self, ios_parser: CiscoIOSParser) -> None:
        assert ios_parser.can_parse("Lorem ipsum dolor sit amet\nconsectetur") is False


# ---------------------------------------------------------------------------
# 2. Hostname & version
# ---------------------------------------------------------------------------

class TestHostnameVersion:
    @pytest.mark.asyncio
    async def test_hostname_minimal(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        assert result.device.hostname == "ROUTER-01"

    @pytest.mark.asyncio
    async def test_hostname_full(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        assert result.device.hostname == "CORE-SW-01"

    @pytest.mark.asyncio
    async def test_version_extracted(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        assert result.device.os_version == "15.2"

    @pytest.mark.asyncio
    async def test_version_full(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        assert result.device.os_version == "16.9"

    @pytest.mark.asyncio
    async def test_vendor_is_cisco_ios(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        assert result.device.vendor == VendorType.CISCO_IOS

    @pytest.mark.asyncio
    async def test_hostname_fallback_when_missing(self, ios_parser: CiscoIOSParser) -> None:
        config = "Building configuration...\nversion 15.2\n!"
        result = await ios_parser.parse(config)
        assert result.device.hostname == "unknown"
        assert len(result.warnings) > 0


# ---------------------------------------------------------------------------
# 3. Interface parsing
# ---------------------------------------------------------------------------

class TestInterfaceParsing:
    @pytest.mark.asyncio
    async def test_interface_count_minimal(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        assert len(result.device.interfaces) == 4  # GE0/0, GE0/1, Lo0, GE0/2

    @pytest.mark.asyncio
    async def test_l3_interface_ip(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        wan = result.device.get_interface("GigabitEthernet0/0")
        assert wan is not None
        assert wan.ip_address == "203.0.113.1"
        assert wan.subnet_mask == "255.255.255.0"
        assert wan.prefix_length == 24

    @pytest.mark.asyncio
    async def test_interface_description(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        wan = result.device.get_interface("GigabitEthernet0/0")
        assert wan is not None
        assert wan.description == "WAN Link"

    @pytest.mark.asyncio
    async def test_interface_speed_duplex(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        wan = result.device.get_interface("GigabitEthernet0/0")
        assert wan is not None
        assert wan.speed == 1000
        assert wan.duplex == "full"

    @pytest.mark.asyncio
    async def test_admin_down_interface(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        iface = result.device.get_interface("GigabitEthernet0/2")
        assert iface is not None
        assert iface.admin_status is False
        assert iface.status == InterfaceStatus.ADMIN_DOWN

    @pytest.mark.asyncio
    async def test_loopback_type(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        lo = result.device.get_interface("Loopback0")
        assert lo is not None
        assert lo.interface_type == InterfaceType.LOOPBACK
        assert lo.is_loopback is True

    @pytest.mark.asyncio
    async def test_trunk_interface(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        uplink = result.device.get_interface("GigabitEthernet1/0/1")
        assert uplink is not None
        assert uplink.switchport_mode == SwitchportMode.TRUNK
        assert 10 in uplink.trunk_vlans
        assert 20 in uplink.trunk_vlans
        assert 30 in uplink.trunk_vlans
        assert 32 in uplink.trunk_vlans
        assert uplink.native_vlan == 99

    @pytest.mark.asyncio
    async def test_access_interface(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        srv = result.device.get_interface("GigabitEthernet1/0/2")
        assert srv is not None
        assert srv.switchport_mode == SwitchportMode.ACCESS
        assert srv.access_vlan == 10

    @pytest.mark.asyncio
    async def test_vlan_interface_mtu(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        vlan10 = result.device.get_interface("Vlan10")
        assert vlan10 is not None
        assert vlan10.mtu == 9000

    @pytest.mark.asyncio
    async def test_cidr_notation_property(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        wan = result.device.get_interface("GigabitEthernet0/0")
        assert wan is not None
        assert wan.cidr_notation == "203.0.113.1/24"


# ---------------------------------------------------------------------------
# 4. VLAN parsing
# ---------------------------------------------------------------------------

class TestVLANParsing:
    @pytest.mark.asyncio
    async def test_vlan_count(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        assert len(result.device.vlans) == 2

    @pytest.mark.asyncio
    async def test_vlan_name(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        vlan10 = result.device.get_vlan(10)
        assert vlan10 is not None
        assert vlan10.name == "SERVERS"

    @pytest.mark.asyncio
    async def test_vlan_suspend_state(self, ios_parser: CiscoIOSParser) -> None:
        from ..models.vlan import VLANStatus
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        vlan20 = result.device.get_vlan(20)
        assert vlan20 is not None
        assert vlan20.status == VLANStatus.SUSPEND


# ---------------------------------------------------------------------------
# 5. Static routes
# ---------------------------------------------------------------------------

class TestStaticRoutes:
    @pytest.mark.asyncio
    async def test_default_route(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        default = next(
            (r for r in result.device.static_routes if r.network == "0.0.0.0"), None
        )
        assert default is not None
        assert default.next_hop == "203.0.113.254"
        assert default.protocol == RouteProtocol.STATIC

    @pytest.mark.asyncio
    async def test_route_with_metric(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        route = next(
            (r for r in result.device.static_routes if r.network == "192.168.100.0"), None
        )
        assert route is not None
        assert route.metric == 100

    @pytest.mark.asyncio
    async def test_vrf_route(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        route = next(
            (r for r in result.device.static_routes if r.vrf == "MGMT"), None
        )
        assert route is not None
        assert route.network == "172.16.0.0"


# ---------------------------------------------------------------------------
# 6. OSPF parsing
# ---------------------------------------------------------------------------

class TestOSPFParsing:
    @pytest.mark.asyncio
    async def test_ospf_process_count(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        assert len(result.device.ospf_processes) == 1

    @pytest.mark.asyncio
    async def test_ospf_process_id(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        ospf = result.device.ospf_processes[0]
        assert ospf.process_id == 1

    @pytest.mark.asyncio
    async def test_ospf_router_id(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        ospf = result.device.ospf_processes[0]
        assert ospf.router_id == "1.1.1.1"

    @pytest.mark.asyncio
    async def test_ospf_networks(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        ospf = result.device.ospf_processes[0]
        assert len(ospf.networks) == 2
        areas = {n.area for n in ospf.networks}
        assert "0" in areas

    @pytest.mark.asyncio
    async def test_ospf_passive_interface(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        ospf = result.device.ospf_processes[0]
        assert "GigabitEthernet1/0/2" in ospf.passive_interfaces

    @pytest.mark.asyncio
    async def test_ospf_redistribution(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        ospf = result.device.ospf_processes[0]
        assert len(ospf.redistributions) == 1
        redist = ospf.redistributions[0]
        assert redist.source_protocol == "static"
        assert redist.metric == 20
        assert redist.metric_type == 2


# ---------------------------------------------------------------------------
# 7. BGP parsing
# ---------------------------------------------------------------------------

class TestBGPParsing:
    @pytest.mark.asyncio
    async def test_bgp_process_count(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        assert len(result.device.bgp_processes) == 1

    @pytest.mark.asyncio
    async def test_bgp_local_as(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        bgp = result.device.bgp_processes[0]
        assert bgp.local_as == 65001

    @pytest.mark.asyncio
    async def test_bgp_router_id(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        bgp = result.device.bgp_processes[0]
        assert bgp.router_id == "1.1.1.1"

    @pytest.mark.asyncio
    async def test_bgp_neighbor(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        bgp = result.device.bgp_processes[0]
        assert len(bgp.neighbors) == 1
        neighbor = bgp.neighbors[0]
        assert neighbor.address == "203.0.113.254"
        assert neighbor.remote_as == 65002
        assert neighbor.description == "ISP-Peer"
        assert neighbor.next_hop_self is True
        assert neighbor.route_map_in == "RM-IN"
        assert neighbor.route_map_out == "RM-OUT"

    @pytest.mark.asyncio
    async def test_bgp_network(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        bgp = result.device.bgp_processes[0]
        assert len(bgp.networks) == 1
        assert bgp.networks[0].network == "10.0.0.0"
        assert bgp.networks[0].mask == "255.0.0.0"


# ---------------------------------------------------------------------------
# 8. ACL parsing
# ---------------------------------------------------------------------------

class TestACLParsing:
    @pytest.mark.asyncio
    async def test_named_extended_acl(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        acl = next((a for a in result.device.acls if a.name == "PERMIT-WEB"), None)
        assert acl is not None
        assert acl.acl_type == ACLType.NAMED_EXTENDED
        assert acl.entry_count == 3

    @pytest.mark.asyncio
    async def test_named_extended_acl_entries(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        acl = next((a for a in result.device.acls if a.name == "PERMIT-WEB"), None)
        assert acl is not None
        # First entry: permit tcp
        entry = acl.entries[0]
        assert entry.action == ACLAction.PERMIT
        assert entry.sequence == 10

    @pytest.mark.asyncio
    async def test_named_standard_acl(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        acl = next((a for a in result.device.acls if a.name == "MGMT-ACCESS"), None)
        assert acl is not None
        assert acl.acl_type == ACLType.NAMED_STANDARD

    @pytest.mark.asyncio
    async def test_numbered_standard_acl(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        acl = next((a for a in result.device.acls if a.name == "10"), None)
        assert acl is not None


# ---------------------------------------------------------------------------
# 9. NAT parsing
# ---------------------------------------------------------------------------

class TestNATParsing:
    @pytest.mark.asyncio
    async def test_static_nat(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        static = next(
            (r for r in result.device.nat_rules if r.nat_type == NATType.STATIC), None
        )
        assert static is not None
        assert static.source_network == "192.168.1.10"
        assert static.translated_address == "203.0.113.10"

    @pytest.mark.asyncio
    async def test_pat_nat(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(FULL_IOS_CONFIG)
        pat = next(
            (r for r in result.device.nat_rules if r.nat_type == NATType.PAT), None
        )
        assert pat is not None
        assert pat.overload is True


# ---------------------------------------------------------------------------
# 10. ParsedDevice metadata
# ---------------------------------------------------------------------------

class TestParsedDeviceMetadata:
    @pytest.mark.asyncio
    async def test_parser_version_set(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        assert result.parser_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_parsing_duration_positive(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        assert result.parsing_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_success_property(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_raw_config_preserved(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        assert result.device.raw_config == MINIMAL_IOS_CONFIG


# ---------------------------------------------------------------------------
# 11. Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_empty_config_raises(self, ios_parser: CiscoIOSParser) -> None:
        with pytest.raises(ParserError):
            await ios_parser.parse("")

    @pytest.mark.asyncio
    async def test_whitespace_only_raises(self, ios_parser: CiscoIOSParser) -> None:
        with pytest.raises(ParserError):
            await ios_parser.parse("   \n\t  ")

    @pytest.mark.asyncio
    async def test_partial_config_no_crash(self, ios_parser: CiscoIOSParser) -> None:
        """Parser should not crash on partial / truncated configs."""
        partial = "Building configuration...\nhostname PARTIAL\ninterface Gi0/0\n"
        result = await ios_parser.parse(partial)
        assert result.device.hostname == "PARTIAL"

    @pytest.mark.asyncio
    async def test_active_interface_count(self, ios_parser: CiscoIOSParser) -> None:
        result = await ios_parser.parse(MINIMAL_IOS_CONFIG)
        # GE0/2 is shut, so active count should be 3
        assert result.device.active_interface_count == 3
