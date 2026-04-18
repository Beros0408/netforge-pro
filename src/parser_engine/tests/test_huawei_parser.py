"""
Tests for Huawei VRP parser.

Comprehensive test suite covering all parser functionality.
"""
import pytest
from src.parser_engine.parsers.huawei.vrp_parser import HuaweiVRPParser
from src.parser_engine.parsers.base_parser import ParserError
from src.parser_engine.models.device import VendorType, OSType
from src.parser_engine.models.interface import InterfaceType, SwitchportMode, InterfaceStatus
from src.parser_engine.models.vlan import VLANStatus
from src.parser_engine.models.routing import RouteProtocol
from src.parser_engine.models.security import ACLAction, ACLType


class TestHuaweiDetection:
    """Test vendor/OS detection capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HuaweiVRPParser()

    def test_can_parse_huawei_vrp_version(self):
        """Test detection of Huawei VRP version strings."""
        config = """
#
sysname TEST-ROUTER
#
return
"""
        assert self.parser.can_parse(config)

    def test_can_parse_huawei_model_comment(self):
        """Test detection via model comments."""
        config = """
#Huawei Versatile Routing Platform Software
#VRP (R) software, Version 8.180 (CE12800 V200R019C10SPC800)
#Copyright (C) 2012-2020 Huawei Technologies Co., Ltd.
#
sysname TEST-ROUTER
#
return
"""
        assert self.parser.can_parse(config)

    def test_can_parse_huawei_interface_config(self):
        """Test detection via Huawei-specific interface syntax."""
        config = """
#
interface GigabitEthernet0/0/1
 description Test Interface
 ip address 192.168.1.1 255.255.255.0
#
return
"""
        assert self.parser.can_parse(config)

    def test_cannot_parse_cisco_ios(self):
        """Test rejection of Cisco IOS configs."""
        config = """
!
hostname TEST-ROUTER
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
!
end
"""
        assert not self.parser.can_parse(config)

    def test_cannot_parse_arista_eos(self):
        """Test rejection of Arista EOS configs."""
        config = """
! EOS version 4.28.3M
hostname TEST-SWITCH
!
interface Ethernet1
   description Test Interface
   ip address 192.168.1.1/24
!
end
"""
        assert not self.parser.can_parse(config)

    def test_cannot_parse_empty_config(self):
        """Test rejection of empty configs."""
        config = ""
        assert not self.parser.can_parse(config)


class TestHuaweiDeviceInfo:
    """Test device information parsing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HuaweiVRPParser()
        self.config = """
#
sysname TEST-ROUTER
#
return
"""
        self.parsed = None

    @pytest.fixture(autouse=True)
    def parse_config(self):
        """Parse config once for all tests."""
        import asyncio
        async def parse():
            return await self.parser.parse(self.config)
        self.parsed = asyncio.run(parse())

    def test_hostname_extraction(self):
        """Test hostname is correctly extracted."""
        assert self.parsed.device.hostname == "TEST-ROUTER"

    def test_vendor_type(self):
        """Test vendor type is set correctly."""
        assert self.parsed.device.vendor == VendorType.HUAWEI_VRP

    def test_os_type(self):
        """Test OS type is set correctly."""
        assert self.parsed.device.os_type == OSType.VRP

    def test_os_version_unknown_when_not_present(self):
        """Test OS version is unknown when not in config."""
        assert self.parsed.device.os_version == "unknown"


class TestHuaweiInterfaces:
    """Test interface parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HuaweiVRPParser()
        self.config = """
#
sysname TEST-ROUTER
#
interface GigabitEthernet0/0/1
 description Uplink to Core
 port link-type trunk
 port trunk allow-pass vlan 10 20 30
#
interface GigabitEthernet0/0/2
 description Access Port
 port link-type access
 port default vlan 100
#
interface Vlanif10
 description SVI for VLAN 10
 ip address 192.168.10.1 255.255.255.0
#
interface LoopBack0
 description Management Loopback
 ip address 10.0.0.1 255.255.255.255
#
interface Eth-Trunk1
 description Port Channel
 mode lacp
#
interface GigabitEthernet0/0/3
 description Shutdown Interface
 shutdown
#
return
"""
        self.parsed = None

    @pytest.fixture(autouse=True)
    def parse_config(self):
        """Parse config once for all tests."""
        import asyncio
        async def parse():
            return await self.parser.parse(self.config)
        self.parsed = asyncio.run(parse())

    def test_interface_count(self):
        """Test correct number of interfaces parsed."""
        assert len(self.parsed.device.interfaces) == 6

    def test_trunk_interface_mode(self):
        """Test trunk interface mode detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "GigabitEthernet0/0/1")
        assert iface.switchport_mode == SwitchportMode.TRUNK

    def test_trunk_interface_vlans(self):
        """Test trunk interface allowed VLANs."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "GigabitEthernet0/0/1")
        assert 10 in iface.trunk_vlans
        assert 20 in iface.trunk_vlans
        assert 30 in iface.trunk_vlans

    def test_access_interface_mode(self):
        """Test access interface mode detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "GigabitEthernet0/0/2")
        assert iface.switchport_mode == SwitchportMode.ACCESS

    def test_access_interface_vlan(self):
        """Test access interface VLAN assignment."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "GigabitEthernet0/0/2")
        assert iface.access_vlan == 100

    def test_svi_interface_type(self):
        """Test SVI interface type detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Vlanif10")
        assert iface.interface_type == InterfaceType.VLAN

    def test_svi_interface_ip(self):
        """Test SVI interface IP address."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Vlanif10")
        assert iface.ip_address == "192.168.10.1"
        assert iface.subnet_mask == "255.255.255.0"
        assert iface.prefix_length == 24

    def test_loopback_interface_type(self):
        """Test loopback interface type detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "LoopBack0")
        assert iface.interface_type == InterfaceType.LOOPBACK

    def test_loopback_interface_ip(self):
        """Test loopback interface IP address."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "LoopBack0")
        assert iface.ip_address == "10.0.0.1"
        assert iface.subnet_mask == "255.255.255.255"
        assert iface.prefix_length == 32

    def test_port_channel_interface_type(self):
        """Test port channel interface type detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Eth-Trunk1")
        assert iface.interface_type == InterfaceType.PORT_CHANNEL

    def test_shutdown_interface_status(self):
        """Test shutdown interface admin status."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "GigabitEthernet0/0/3")
        assert not iface.admin_status
        assert iface.status == InterfaceStatus.ADMIN_DOWN

    def test_interface_descriptions(self):
        """Test interface descriptions are parsed."""
        descriptions = {i.name: i.description for i in self.parsed.device.interfaces}
        assert descriptions["GigabitEthernet0/0/1"] == "Uplink to Core"
        assert descriptions["GigabitEthernet0/0/2"] == "Access Port"
        assert descriptions["Vlanif10"] == "SVI for VLAN 10"
        assert descriptions["LoopBack0"] == "Management Loopback"
        assert descriptions["Eth-Trunk1"] == "Port Channel"
        assert descriptions["GigabitEthernet0/0/3"] == "Shutdown Interface"


class TestHuaweiVLANs:
    """Test VLAN parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HuaweiVRPParser()
        self.config = """
#
sysname TEST-SWITCH
#
vlan batch 10 20 30
#
vlan 100
 name USER_VLAN
 description User Access VLAN
#
vlan 200
 name SERVER_VLAN
#
return
"""
        self.parsed = None

    @pytest.fixture(autouse=True)
    def parse_config(self):
        """Parse config once for all tests."""
        import asyncio
        async def parse():
            return await self.parser.parse(self.config)
        self.parsed = asyncio.run(parse())

    def test_vlan_count(self):
        """Test correct number of VLANs parsed."""
        assert len(self.parsed.device.vlans) == 5

    def test_batch_vlan_ids(self):
        """Test batch VLAN creation."""
        vlan_ids = {v.vlan_id for v in self.parsed.device.vlans}
        assert 10 in vlan_ids
        assert 20 in vlan_ids
        assert 30 in vlan_ids

    def test_batch_vlan_names(self):
        """Test batch VLAN default names."""
        vlan_names = {v.vlan_id: v.name for v in self.parsed.device.vlans}
        assert vlan_names[10] == "VLAN0010"
        assert vlan_names[20] == "VLAN0020"
        assert vlan_names[30] == "VLAN0030"

    def test_named_vlan_name(self):
        """Test explicitly named VLAN."""
        vlan = next(v for v in self.parsed.device.vlans if v.vlan_id == 100)
        assert vlan.name == "USER_VLAN"

    def test_named_vlan_description(self):
        """Test VLAN description parsing."""
        vlan = next(v for v in self.parsed.device.vlans if v.vlan_id == 100)
        assert vlan.description == "User Access VLAN"

    def test_vlan_without_description(self):
        """Test VLAN without description."""
        vlan = next(v for v in self.parsed.device.vlans if v.vlan_id == 200)
        assert vlan.name == "SERVER_VLAN"
        assert vlan.description is None

    def test_vlan_status_active(self):
        """Test VLAN status is active by default."""
        for vlan in self.parsed.device.vlans:
            assert vlan.status == VLANStatus.ACTIVE


class TestHuaweiRouting:
    """Test routing protocol parsing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HuaweiVRPParser()
        self.config = """
#
sysname TEST-ROUTER
#
ip route-static 0.0.0.0 0.0.0.0 192.168.1.254
ip route-static 10.0.0.0 255.255.0.0 10.1.1.1 preference 200
ip route-static vpn-instance PROD 192.168.0.0 255.255.255.0 192.168.1.1
#
ospf 100 router-id 10.0.0.1
 area 0.0.0.0
  network 192.168.10.0 0.0.0.255
  network 192.168.20.0 0.0.0.255
#
bgp 65001
 router-id 10.0.0.1
 peer 10.0.0.100 as-number 65000
 peer 10.0.0.100 description SPINE-RR
 peer 10.0.0.200 as-number 65002
#
return
"""
        self.parsed = None

    @pytest.fixture(autouse=True)
    def parse_config(self):
        """Parse config once for all tests."""
        import asyncio
        async def parse():
            return await self.parser.parse(self.config)
        self.parsed = asyncio.run(parse())

    def test_static_route_count(self):
        """Test correct number of static routes."""
        assert len(self.parsed.device.static_routes) == 3

    def test_default_route(self):
        """Test default route parsing."""
        route = next(r for r in self.parsed.device.static_routes if r.network == "0.0.0.0/0")
        assert route.next_hop == "192.168.1.254"
        assert route.protocol == RouteProtocol.STATIC
        assert route.distance == 60  # Huawei default

    def test_static_route_with_preference(self):
        """Test static route with custom preference."""
        route = next(r for r in self.parsed.device.static_routes if r.network == "10.0.0.0/16")
        assert route.next_hop == "10.1.1.1"
        assert route.distance == 200

    def test_static_route_with_vrf(self):
        """Test static route in VRF."""
        route = next(r for r in self.parsed.device.static_routes if r.network == "192.168.0.0/24")
        assert route.next_hop == "192.168.1.1"
        assert route.vrf == "PROD"

    def test_ospf_process_count(self):
        """Test OSPF process count."""
        assert len(self.parsed.device.ospf_processes) == 1

    def test_ospf_process_id(self):
        """Test OSPF process ID."""
        ospf = self.parsed.device.ospf_processes[0]
        assert ospf.process_id == 100

    def test_ospf_router_id(self):
        """Test OSPF router ID."""
        ospf = self.parsed.device.ospf_processes[0]
        assert ospf.router_id == "10.0.0.1"

    def test_ospf_networks(self):
        """Test OSPF network statements."""
        ospf = self.parsed.device.ospf_processes[0]
        assert len(ospf.networks) == 2
        networks = {n.network for n in ospf.networks}
        assert "192.168.10.0/24" in networks
        assert "192.168.20.0/24" in networks

    def test_ospf_area(self):
        """Test OSPF area assignment."""
        ospf = self.parsed.device.ospf_processes[0]
        for network in ospf.networks:
            assert network.area == "0.0.0.0"

    def test_bgp_process_count(self):
        """Test BGP process count."""
        assert len(self.parsed.device.bgp_processes) == 1

    def test_bgp_asn(self):
        """Test BGP AS number."""
        bgp = self.parsed.device.bgp_processes[0]
        assert bgp.local_as == 65001

    def test_bgp_router_id(self):
        """Test BGP router ID."""
        bgp = self.parsed.device.bgp_processes[0]
        assert bgp.router_id == "10.0.0.1"

    def test_bgp_neighbor_count(self):
        """Test BGP neighbor count."""
        bgp = self.parsed.device.bgp_processes[0]
        assert len(bgp.neighbors) == 2

    def test_bgp_neighbor_asn(self):
        """Test BGP neighbor AS numbers."""
        bgp = self.parsed.device.bgp_processes[0]
        asns = {n.ip: n.remote_as for n in bgp.neighbors}
        assert asns["10.0.0.100"] == 65000
        assert asns["10.0.0.200"] == 65002

    def test_bgp_neighbor_description(self):
        """Test BGP neighbor description."""
        bgp = self.parsed.device.bgp_processes[0]
        neighbor = next(n for n in bgp.neighbors if n.ip == "10.0.0.100")
        assert neighbor.description == "SPINE-RR"

    def test_bgp_neighbor_without_description(self):
        """Test BGP neighbor without description."""
        bgp = self.parsed.device.bgp_processes[0]
        neighbor = next(n for n in bgp.neighbors if n.ip == "10.0.0.200")
        assert neighbor.description is None


class TestHuaweiVRF:
    """Test VRF parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HuaweiVRPParser()
        self.config = """
#
sysname TEST-ROUTER
#
ip vpn-instance PROD
 ipv4-family
  route-distinguisher 65001:100
  vpn-target 65001:100 export-extcommunity
  vpn-target 65001:200 import-extcommunity
#
ip vpn-instance MGMT
 ipv4-family
  route-distinguisher 65001:999
#
return
"""
        self.parsed = None

    @pytest.fixture(autouse=True)
    def parse_config(self):
        """Parse config once for all tests."""
        import asyncio
        async def parse():
            return await self.parser.parse(self.config)
        self.parsed = asyncio.run(parse())

    def test_vrf_count(self):
        """Test correct number of VRFs parsed."""
        assert len(self.parsed.device.vrfs) == 2

    def test_vrf_names(self):
        """Test VRF names are parsed."""
        names = {vrf.name for vrf in self.parsed.device.vrfs}
        assert "PROD" in names
        assert "MGMT" in names

    def test_vrf_rd_prod(self):
        """Test VRF RD for PROD."""
        vrf = next(v for v in self.parsed.device.vrfs if v.name == "PROD")
        assert vrf.rd == "65001:100"

    def test_vrf_rd_mgmt(self):
        """Test VRF RD for MGMT."""
        vrf = next(v for v in self.parsed.device.vrfs if v.name == "MGMT")
        assert vrf.rd == "65001:999"

    def test_vrf_rt_export(self):
        """Test VRF export RT."""
        vrf = next(v for v in self.parsed.device.vrfs if v.name == "PROD")
        assert "65001:100" in vrf.rt_export

    def test_vrf_rt_import(self):
        """Test VRF import RT."""
        vrf = next(v for v in self.parsed.device.vrfs if v.name == "PROD")
        assert "65001:200" in vrf.rt_import

    def test_vrf_without_rt(self):
        """Test VRF without RT statements."""
        vrf = next(v for v in self.parsed.device.vrfs if v.name == "MGMT")
        assert len(vrf.rt_export) == 0
        assert len(vrf.rt_import) == 0


class TestHuaweiACL:
    """Test ACL parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HuaweiVRPParser()
        self.config = """
#
sysname TEST-ROUTER
#
acl number 3000
 rule 5 permit ip source 192.168.1.0 0.0.0.255 destination 10.0.0.0 0.0.255.255
 rule 10 deny ip source 172.16.0.0 0.0.255.255
#
acl number 3001
 description Test ACL
 rule 5 permit tcp source 10.0.0.1 0 destination-port eq 80
#
return
"""
        self.parsed = None

    @pytest.fixture(autouse=True)
    def parse_config(self):
        """Parse config once for all tests."""
        import asyncio
        async def parse():
            return await self.parser.parse(self.config)
        self.parsed = asyncio.run(parse())

    def test_acl_count(self):
        """Test correct number of ACLs parsed."""
        assert len(self.parsed.device.acls) == 2

    def test_acl_names(self):
        """Test ACL names are parsed."""
        names = {acl.name for acl in self.parsed.device.acls}
        assert "3000" in names
        assert "3001" in names

    def test_acl_type(self):
        """Test ACL type is IPv4 extended."""
        for acl in self.parsed.device.acls:
            assert acl.type == ACLType.IPV4_EXTENDED

    def test_acl_3000_entries(self):
        """Test ACL 3000 entries."""
        acl = next(a for a in self.parsed.device.acls if a.name == "3000")
        assert len(acl.entries) == 2

    def test_acl_3000_permit_entry(self):
        """Test ACL 3000 permit entry."""
        acl = next(a for a in self.parsed.device.acls if a.name == "3000")
        entry = next(e for e in acl.entries if e.sequence == 5)
        assert entry.action == ACLAction.PERMIT
        assert entry.source == "192.168.1.0 0.0.0.255"
        assert entry.destination == "10.0.0.0 0.0.255.255"

    def test_acl_3000_deny_entry(self):
        """Test ACL 3000 deny entry."""
        acl = next(a for a in self.parsed.device.acls if a.name == "3000")
        entry = next(e for e in acl.entries if e.sequence == 10)
        assert entry.action == ACLAction.DENY
        assert entry.source == "172.16.0.0 0.0.255.255"

    def test_acl_3001_description(self):
        """Test ACL description."""
        acl = next(a for a in self.parsed.device.acls if a.name == "3001")
        assert acl.description == "Test ACL"

    def test_acl_3001_tcp_entry(self):
        """Test ACL 3001 TCP entry."""
        acl = next(a for a in self.parsed.device.acls if a.name == "3001")
        entry = next(e for e in acl.entries if e.sequence == 5)
        assert entry.action == ACLAction.PERMIT
        assert entry.protocol == "tcp"
        assert entry.source == "10.0.0.1 0"
        assert "destination-port eq 80" in entry.destination


class TestHuaweiNAT:
    """Test NAT parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HuaweiVRPParser()
        self.config = """
#
sysname TEST-ROUTER
#
nat address-group 1 192.168.100.1 192.168.100.10
#
interface GigabitEthernet0/0/1
 nat outbound 2000 address-group 1
#
acl number 2000
 rule 5 permit ip source 10.0.0.0 0.0.255.255
#
return
"""
        self.parsed = None

    @pytest.fixture(autouse=True)
    def parse_config(self):
        """Parse config once for all tests."""
        import asyncio
        async def parse():
            return await self.parser.parse(self.config)
        self.parsed = asyncio.run(parse())

    def test_nat_rule_count(self):
        """Test NAT rule count."""
        assert len(self.parsed.device.nat_rules) == 1

    def test_nat_rule_type(self):
        """Test NAT rule type."""
        nat_rule = self.parsed.device.nat_rules[0]
        assert nat_rule.rule_type == "outbound"

    def test_nat_rule_acl(self):
        """Test NAT rule ACL reference."""
        nat_rule = self.parsed.device.nat_rules[0]
        assert nat_rule.acl_name == "2000"

    def test_nat_address_group(self):
        """Test NAT address group."""
        nat_rule = self.parsed.device.nat_rules[0]
        assert nat_rule.address_group == "1"


class TestHuaweiUtilities:
    """Test utility functions."""

    def test_normalize_interface_name(self):
        """Test interface name normalization."""
        parser = HuaweiVRPParser()
        # Test various interface name formats
        assert parser._normalize_interface_name("GigabitEthernet0/0/1") == "ge0/0/1"
        assert parser._normalize_interface_name("Eth-Trunk1") == "et1"
        assert parser._normalize_interface_name("Vlanif10") == "vl10"
        assert parser._normalize_interface_name("LoopBack0") == "lo0"

    def test_parse_vlan_range_single(self):
        """Test parsing single VLAN."""
        from src.parser_engine.models.vlan import parse_vlan_range
        result = parse_vlan_range("10")
        assert result == [10]

    def test_parse_vlan_range_multiple(self):
        """Test parsing multiple VLANs."""
        from src.parser_engine.models.vlan import parse_vlan_range
        result = parse_vlan_range("10,20,30")
        assert set(result) == {10, 20, 30}

    def test_parse_vlan_range_range(self):
        """Test parsing VLAN range."""
        from src.parser_engine.models.vlan import parse_vlan_range
        result = parse_vlan_range("10-15")
        assert result == list(range(10, 16))

    def test_parse_vlan_range_mixed(self):
        """Test parsing mixed VLAN specification."""
        from src.parser_engine.models.vlan import parse_vlan_range
        result = parse_vlan_range("10,20-22,30")
        assert set(result) == {10, 20, 21, 22, 30}


# Minimal config fixture for edge case testing
@pytest.fixture
def minimal_config():
    """Minimal Huawei config for edge case testing."""
    return """
#
sysname MINIMAL
#
return
"""


@pytest.fixture
def full_config():
    """Full Huawei config with all features for comprehensive testing."""
    return """
#Huawei Versatile Routing Platform Software
#VRP (R) software, Version 8.180 (CE12800 V200R019C10SPC800)
#Copyright (C) 2012-2020 Huawei Technologies Co., Ltd.
#
sysname FULL-TEST-ROUTER
#
interface GigabitEthernet0/0/1
 description Trunk Uplink
 port link-type trunk
 port trunk allow-pass vlan 10 20 30 40-50
#
interface GigabitEthernet0/0/2
 description Access Port
 port link-type access
 port default vlan 100
#
interface Vlanif10
 description Management SVI
 ip address 192.168.10.1 255.255.255.0
#
interface Vlanif20
 description User SVI
 ip address 192.168.20.1 255.255.255.0
 vrf forwarding PROD
#
interface LoopBack0
 description Router ID Loopback
 ip address 10.0.0.1 255.255.255.255
#
interface Eth-Trunk1
 description LACP Port Channel
 mode lacp
#
vlan batch 10 20 30 40 50 100
#
vlan 200
 name SERVER_VLAN
#
ip route-static 0.0.0.0 0.0.0.0 192.168.1.254
ip route-static 10.0.0.0 255.255.0.0 10.1.1.1 preference 150
ip route-static vpn-instance PROD 172.16.0.0 255.255.255.0 172.16.1.1
#
ospf 100 router-id 10.0.0.1
 area 0.0.0.0
  network 192.168.10.0 0.0.0.255
  network 192.168.20.0 0.0.0.255
 area 0.0.0.1
  network 172.16.0.0 0.0.255.255
#
bgp 65001
 router-id 10.0.0.1
 peer 10.0.0.100 as-number 65000
 peer 10.0.0.100 description SPINE-RR
 peer 10.0.0.200 as-number 65002
 peer 10.0.0.200 description LEAF-01
 peer 10.0.0.201 as-number 65002
#
ip vpn-instance PROD
 ipv4-family
  route-distinguisher 65001:100
  vpn-target 65001:100 export-extcommunity
  vpn-target 65001:200 import-extcommunity
#
ip vpn-instance MGMT
 ipv4-family
  route-distinguisher 65001:999
#
acl number 3000
 description Data Center ACL
 rule 5 permit ip source 192.168.0.0 0.0.255.255 destination 10.0.0.0 0.255.255.255
 rule 10 deny ip source 172.16.0.0 0.0.255.255
 rule 15 permit tcp source 10.0.0.1 0 destination 192.168.1.1 0 destination-port eq 443
#
nat address-group 1 192.168.100.1 192.168.100.10
#
interface GigabitEthernet0/0/3
 nat outbound 3000 address-group 1
#
return
"""

MINIMAL_VRP_CONFIG = """\
#Huawei Versatile Routing Platform Software
#VRP (R) software, Version 8.180 (CE12800 V200R019C10SPC800)
#
sysname HUAWEI-01
#
interface GigabitEthernet0/0/1
 description WAN Link
 ip address 203.0.113.1 255.255.255.0
#
interface GigabitEthernet0/0/2
 description LAN
 ip address 192.168.1.1 255.255.255.0
#
interface LoopBack0
 ip address 10.0.0.1 255.255.255.255
#
return
"""

VRP_CONFIG_WITH_VLANS = """\
#
sysname HUAWEI-SW
#
vlan 10
 name MANAGEMENT
#
vlan 20
 name DATA
#
vlan 30
 name VOICE
#
interface GigabitEthernet0/0/1
 description Trunk to Core
 port link-type trunk
 port trunk allow-pass vlan 10 20 30
#
interface GigabitEthernet0/0/2
 description Access Port
 port link-type access
 port default vlan 10
#
return
"""

VRP_CONFIG_WITH_ROUTING = """\
#
sysname HUAWEI-RTR
#
ip route-static 0.0.0.0 0.0.0.0 203.0.113.254
ip route-static 192.168.2.0 255.255.255.0 10.0.0.2
#
ospf 1
 router-id 10.0.0.1
 network 10.0.0.0 0.255.255.255 area 0.0.0.0
 network 192.168.1.0 0.0.0.255 area 0.0.0.0
#
bgp 65001
 router-id 10.0.0.1
 peer 10.0.0.2 as-number 65002
#
return
"""

VRP_CONFIG_WITH_ACL = """\
#
sysname HUAWEI-FW
#
acl number 3000
 rule 5 permit ip source 192.168.1.0 0.0.0.255 destination 10.0.0.0 0.255.255.255
 rule 10 deny ip source any destination any
#
interface GigabitEthernet0/0/1
 description Outside
 ip address 203.0.113.1 255.255.255.0
 traffic-filter inbound acl 3000
#
return
"""

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHuaweiVRPParser:
    """Test Huawei VRP parser functionality."""

    @pytest.fixture
    def parser(self) -> HuaweiVRPParser:
        """Return a fresh parser instance."""
        return HuaweiVRPParser()

    # ------------------------------------------------------------------
    # Vendor detection tests
    # ------------------------------------------------------------------

    def test_can_parse_minimal_config(self, parser: HuaweiVRPParser):
        """Test detection of minimal Huawei VRP config."""
        assert parser.can_parse(MINIMAL_VRP_CONFIG)

    def test_can_parse_with_vlans(self, parser: HuaweiVRPParser):
        """Test detection of VRP config with VLANs."""
        assert parser.can_parse(VRP_CONFIG_WITH_VLANS)

    def test_cannot_parse_empty_config(self, parser: HuaweiVRPParser):
        """Test rejection of empty config."""
        assert not parser.can_parse("")
        assert not parser.can_parse("   \n\t  ")

    def test_cannot_parse_cisco_config(self, parser: HuaweiVRPParser):
        """Test rejection of Cisco IOS config."""
        cisco_config = "hostname ROUTER-01\ninterface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0"
        assert not parser.can_parse(cisco_config)

    # ------------------------------------------------------------------
    # Basic parsing tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_parse_minimal_config(self, parser: HuaweiVRPParser):
        """Test parsing of minimal VRP config."""
        result = await parser.parse(MINIMAL_VRP_CONFIG)

        assert result.device.hostname == "HUAWEI-01"
        assert result.device.vendor == VendorType.HUAWEI_VRP
        assert "8.180" in result.device.os_version
        assert len(result.device.interfaces) == 3

        # Check interfaces
        ge1 = next(iface for iface in result.device.interfaces if iface.name == "GigabitEthernet0/0/1")
        assert ge1.description == "WAN Link"
        assert "203.0.113.1/24" in ge1.ipv4_addresses
        assert ge1.enabled is True

        ge2 = next(iface for iface in result.device.interfaces if iface.name == "GigabitEthernet0/0/2")
        assert ge2.description == "LAN"
        assert "192.168.1.1/24" in ge2.ipv4_addresses

        lo0 = next(iface for iface in result.device.interfaces if iface.name == "LoopBack0")
        assert "10.0.0.1/32" in lo0.ipv4_addresses

    @pytest.mark.asyncio
    async def test_parse_vlan_config(self, parser: HuaweiVRPParser):
        """Test parsing of VLAN configuration."""
        result = await parser.parse(VRP_CONFIG_WITH_VLANS)

        assert result.device.hostname == "HUAWEI-SW"
        assert len(result.device.vlans) == 3

        # Check VLANs
        vlan10 = next(vlan for vlan in result.device.vlans if vlan.vlan_id == 10)
        assert vlan10.name == "MANAGEMENT"

        vlan20 = next(vlan for vlan in result.device.vlans if vlan.vlan_id == 20)
        assert vlan20.name == "DATA"

        vlan30 = next(vlan for vlan in result.device.vlans if vlan.vlan_id == 30)
        assert vlan30.name == "VOICE"

        # Check interfaces
        trunk_iface = next(iface for iface in result.device.interfaces if iface.name == "GigabitEthernet0/0/1")
        assert trunk_iface.switchport_mode == SwitchportMode.TRUNK
        assert set(trunk_iface.trunk_vlans) == {10, 20, 30}

        access_iface = next(iface for iface in result.device.interfaces if iface.name == "GigabitEthernet0/0/2")
        assert access_iface.switchport_mode == SwitchportMode.ACCESS

    @pytest.mark.asyncio
    async def test_parse_routing_config(self, parser: HuaweiVRPParser):
        """Test parsing of routing configuration."""
        result = await parser.parse(VRP_CONFIG_WITH_ROUTING)

        assert result.device.hostname == "HUAWEI-RTR"

        # Check static routes
        assert len(result.device.static_routes) == 2
        default_route = next(route for route in result.device.static_routes if route.network == "0.0.0.0/0")
        assert default_route.next_hop == "203.0.113.254"

        # Check OSPF
        assert len(result.device.ospf_processes) == 1
        ospf = result.device.ospf_processes[0]
        assert ospf.process_id == 1
        assert ospf.router_id == "10.0.0.1"
        assert len(ospf.networks) == 2

        # Check BGP
        assert len(result.device.bgp_processes) == 1
        bgp = result.device.bgp_processes[0]
        assert bgp.asn == 65001
        assert bgp.router_id == "10.0.0.1"
        assert len(bgp.neighbors) == 1
        assert bgp.neighbors[0].ip == "10.0.0.2"
        assert bgp.neighbors[0].remote_as == 65002

    @pytest.mark.asyncio
    async def test_parse_acl_config(self, parser: HuaweiVRPParser):
        """Test parsing of ACL configuration."""
        result = await parser.parse(VRP_CONFIG_WITH_ACL)

        assert result.device.hostname == "HUAWEI-FW"

        # Check ACLs
        assert len(result.device.acls) == 1
        acl = result.device.acls[0]
        assert acl.name == "3000"
        assert acl.type == ACLType.IPV4_EXTENDED
        assert len(acl.entries) == 2

        permit_rule = next(entry for entry in acl.entries if entry.sequence == 5)
        assert permit_rule.action == ACLAction.PERMIT

        deny_rule = next(entry for entry in acl.entries if entry.sequence == 10)
        assert deny_rule.action == ACLAction.DENY

    # ------------------------------------------------------------------
    # Error handling tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_parse_empty_config_raises_error(self, parser: HuaweiVRPParser):
        """Test that empty config raises ParserError."""
        with pytest.raises(ParserError, match="Configuration is empty"):
            await parser.parse("")

    @pytest.mark.asyncio
    async def test_parse_invalid_config_graceful_handling(self, parser: HuaweiVRPParser):
        """Test graceful handling of invalid config sections."""
        invalid_config = """\
#
sysname TEST
#
interface GigabitEthernet0/0/1
 invalid command that should be ignored
 ip address 192.168.1.1 255.255.255.0
#
return
"""
        result = await parser.parse(invalid_config)
        assert result.device.hostname == "TEST"
        assert len(result.device.interfaces) == 1