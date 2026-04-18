"""
Tests for Arista EOS parser.

Comprehensive test suite covering all parser functionality.
"""
import pytest
from src.parser_engine.parsers.arista.eos_parser import AristaEOSParser
from src.parser_engine.models.device import VendorType, OSType
from src.parser_engine.models.interface import InterfaceType, SwitchportMode, InterfaceStatus
from src.parser_engine.models.vlan import VLANStatus
from src.parser_engine.models.routing import RouteProtocol
from src.parser_engine.models.security import ACLAction, ACLType
from src.parser_engine.parsers.base_parser import ParserError


class TestAristaDetection:
    """Test vendor/OS detection capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AristaEOSParser()

    def test_can_parse_arista_eos_version(self):
        """Test detection of Arista EOS version strings."""
        config = """
! EOS version 4.28.3M
hostname TEST-SWITCH
!
interface Ethernet1
   description Test Interface
!
end
"""
        assert self.parser.can_parse(config)

    def test_can_parse_arista_eos_dash(self):
        """Test detection of EOS- format."""
        config = """
! EOS-4.28.3M
hostname TEST-SWITCH
!
interface Ethernet1
   description Test Interface
!
end
"""
        assert self.parser.can_parse(config)

    def test_can_parse_ceoslab(self):
        """Test detection of cEOSLab."""
        config = """
! cEOSLab version 4.28.3M
hostname TEST-SWITCH
!
interface Ethernet1
   description Test Interface
!
end
"""
        assert self.parser.can_parse(config)

    def test_can_parse_veos(self):
        """Test detection of vEOS."""
        config = """
! vEOS version 4.28.3M
hostname TEST-SWITCH
!
interface Ethernet1
   description Test Interface
!
end
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

    def test_cannot_parse_huawei_vrp(self):
        """Test rejection of Huawei VRP configs."""
        config = """
#
sysname TEST-ROUTER
#
interface GigabitEthernet0/0/1
 ip address 192.168.1.1 255.255.255.0
#
return
"""
        assert not self.parser.can_parse(config)

    def test_cannot_parse_empty_config(self):
        """Test rejection of empty configs."""
        config = ""
        assert not self.parser.can_parse(config)


class TestAristaDeviceInfo:
    """Test device information parsing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AristaEOSParser()
        self.config = """
! EOS version 4.28.3M
! Model: DCS-7050CX3-32S
! Serial Number: SSJ18150206
hostname LEAF-01
!
interface Ethernet1
   description Test Interface
!
end
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
        assert self.parsed.device.hostname == "LEAF-01"

    def test_vendor_type(self):
        """Test vendor type is set correctly."""
        assert self.parsed.device.vendor == VendorType.ARISTA_EOS

    def test_os_version_extraction(self):
        """Test OS version is correctly extracted."""
        assert self.parsed.device.os_version == "4.28.3M"

    def test_model_extraction(self):
        """Test model is extracted from comments."""
        assert self.parsed.device.model == "DCS-7050CX3-32S"

    def test_serial_extraction(self):
        """Test serial number is extracted from comments."""
        assert self.parsed.device.serial_number == "SSJ18150206"


class TestAristaInterfaces:
    """Test interface parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AristaEOSParser()
        self.config = """
! EOS version 4.28.3M
hostname LEAF-01
!
interface Ethernet1
   description Uplink to SPINE-01
   switchport mode trunk
   switchport trunk allowed vlan 10,20,30
   switchport trunk native vlan 1
   mtu 9216
   speed 10g
   duplex full
!
interface Ethernet2
   description Access Port
   switchport mode access
   switchport access vlan 100
!
interface Vlan10
   description SVI for VLAN 10
   ip address 192.168.10.1/24
   vrf forwarding PROD
!
interface Loopback0
   description Management Loopback
   ip address 10.0.0.1/32
!
interface Port-Channel1
   description LACP Port Channel
!
interface Ethernet3
   description Shutdown Interface
   shutdown
!
interface Vxlan1
   description VXLAN Interface
   vxlan source-interface Loopback0
   vxlan vlan 10 vni 10010
   vxlan vlan 20 vni 10020
!
end
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
        assert len(self.parsed.device.interfaces) == 7

    def test_trunk_interface_mode(self):
        """Test trunk interface mode detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Ethernet1")
        assert iface.switchport_mode == SwitchportMode.TRUNK

    def test_trunk_interface_vlans(self):
        """Test trunk interface allowed VLANs."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Ethernet1")
        assert 10 in iface.trunk_vlans
        assert 20 in iface.trunk_vlans
        assert 30 in iface.trunk_vlans

    def test_trunk_native_vlan(self):
        """Test trunk native VLAN."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Ethernet1")
        assert iface.native_vlan == 1

    def test_access_interface_mode(self):
        """Test access interface mode detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Ethernet2")
        assert iface.switchport_mode == SwitchportMode.ACCESS

    def test_access_interface_vlan(self):
        """Test access interface VLAN assignment."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Ethernet2")
        assert iface.access_vlan == 100

    def test_svi_interface_type(self):
        """Test SVI interface type detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Vlan10")
        assert iface.interface_type == InterfaceType.VLAN

    def test_svi_interface_ip(self):
        """Test SVI interface IP address."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Vlan10")
        assert iface.ip_address == "192.168.10.1"
        assert iface.prefix_length == 24

    def test_svi_interface_vrf(self):
        """Test SVI interface VRF assignment."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Vlan10")
        assert iface.vrf == "PROD"

    def test_loopback_interface_type(self):
        """Test loopback interface type detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Loopback0")
        assert iface.interface_type == InterfaceType.LOOPBACK

    def test_loopback_interface_ip(self):
        """Test loopback interface IP address."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Loopback0")
        assert iface.ip_address == "10.0.0.1"
        assert iface.prefix_length == 32

    def test_port_channel_interface_type(self):
        """Test port channel interface type detection."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Port-Channel1")
        assert iface.interface_type == InterfaceType.PORT_CHANNEL

    def test_shutdown_interface_status(self):
        """Test shutdown interface admin status."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Ethernet3")
        assert not iface.admin_status
        assert iface.status == InterfaceStatus.ADMIN_DOWN

    def test_interface_mtu(self):
        """Test interface MTU setting."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Ethernet1")
        assert iface.mtu == 9216

    def test_interface_speed(self):
        """Test interface speed setting."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Ethernet1")
        assert iface.speed == 10000  # 10g converted to Mbps

    def test_interface_duplex(self):
        """Test interface duplex setting."""
        iface = next(i for i in self.parsed.device.interfaces if i.name == "Ethernet1")
        assert iface.duplex == "full"

    def test_interface_descriptions(self):
        """Test interface descriptions are parsed."""
        descriptions = {i.name: i.description for i in self.parsed.device.interfaces}
        assert descriptions["Ethernet1"] == "Uplink to SPINE-01"
        assert descriptions["Ethernet2"] == "Access Port"
        assert descriptions["Vlan10"] == "SVI for VLAN 10"
        assert descriptions["Loopback0"] == "Management Loopback"
        assert descriptions["Port-Channel1"] == "LACP Port Channel"
        assert descriptions["Ethernet3"] == "Shutdown Interface"
        assert descriptions["Vxlan1"] == "VXLAN Interface"


class TestAristaVLANs:
    """Test VLAN parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AristaEOSParser()
        self.config = """
! EOS version 4.28.3M
hostname LEAF-01
!
vlan 10
   name USERS
   state active
!
vlan 20
   name SERVERS
!
vlan 30
   name GUESTS
   state suspend
!
end
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
        assert len(self.parsed.device.vlans) == 3

    def test_vlan_ids(self):
        """Test VLAN IDs are parsed."""
        vlan_ids = {v.vlan_id for v in self.parsed.device.vlans}
        assert vlan_ids == {10, 20, 30}

    def test_vlan_names(self):
        """Test VLAN names are parsed."""
        vlan_names = {v.vlan_id: v.name for v in self.parsed.device.vlans}
        assert vlan_names[10] == "USERS"
        assert vlan_names[20] == "SERVERS"
        assert vlan_names[30] == "GUESTS"

    def test_vlan_status_active(self):
        """Test VLAN active status."""
        vlan = next(v for v in self.parsed.device.vlans if v.vlan_id == 10)
        assert vlan.status == VLANStatus.ACTIVE

    def test_vlan_status_suspend(self):
        """Test VLAN suspend status."""
        vlan = next(v for v in self.parsed.device.vlans if v.vlan_id == 30)
        assert vlan.status == VLANStatus.SUSPEND

    def test_vlan_default_status(self):
        """Test VLAN default status is active."""
        vlan = next(v for v in self.parsed.device.vlans if v.vlan_id == 20)
        assert vlan.status == VLANStatus.ACTIVE


class TestAristaRouting:
    """Test routing protocol parsing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AristaEOSParser()
        self.config = """
! EOS version 4.28.3M
hostname LEAF-01
!
ip route 0.0.0.0/0 192.168.1.254
ip route 10.0.0.0/16 10.1.1.1 200
ip route vrf PROD 172.16.0.0/24 172.16.1.1
!
router ospf 100
   router-id 10.0.0.1
   network 192.168.10.0/24 area 0.0.0.0
   network 192.168.20.0/24 area 0.0.0.0
   redistribute static metric 10 metric-type 1
!
router bgp 65001
   router-id 10.0.0.1
   neighbor 10.0.0.100 remote-as 65000
   neighbor 10.0.0.100 description SPINE-RR
   neighbor 10.0.0.200 remote-as 65002
   neighbor 10.0.0.200 peer group LEAF
   network 192.168.0.0/16
!
end
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
        assert route.distance == 1

    def test_static_route_with_distance(self):
        """Test static route with custom distance."""
        route = next(r for r in self.parsed.device.static_routes if r.network == "10.0.0.0/16")
        assert route.next_hop == "10.1.1.1"
        assert route.distance == 200

    def test_static_route_with_vrf(self):
        """Test static route in VRF."""
        route = next(r for r in self.parsed.device.static_routes if r.network == "172.16.0.0/24")
        assert route.next_hop == "172.16.1.1"
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

    def test_ospf_redistribution(self):
        """Test OSPF redistribution."""
        ospf = self.parsed.device.ospf_processes[0]
        assert len(ospf.redistributions) == 1
        redis = ospf.redistributions[0]
        assert redis.protocol == "static"
        assert redis.metric == 10
        assert redis.metric_type == 1

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

    def test_bgp_neighbor_peer_group(self):
        """Test BGP neighbor peer group."""
        bgp = self.parsed.device.bgp_processes[0]
        neighbor = next(n for n in bgp.neighbors if n.ip == "10.0.0.200")
        assert neighbor.peer_group == "LEAF"

    def test_bgp_networks(self):
        """Test BGP network advertisements."""
        bgp = self.parsed.device.bgp_processes[0]
        assert len(bgp.networks) == 1
        assert bgp.networks[0].network == "192.168.0.0/16"


class TestAristaVRF:
    """Test VRF parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AristaEOSParser()
        self.config = """
! EOS version 4.28.3M
hostname LEAF-01
!
vrf instance PROD
   rd 65001:100
!
vrf instance MGMT
   rd 65001:999
!
end
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


class TestAristaACL:
    """Test ACL parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AristaEOSParser()
        self.config = """
! EOS version 4.28.3M
hostname LEAF-01
!
ip access-list ACL-TEST
   10 permit ip 192.168.1.0/24 10.0.0.0/8
   20 deny tcp 172.16.0.0/16 192.168.0.0/16 eq 23
!
ip access-list extended ACL-EXT
   10 permit tcp 10.0.0.1/32 192.168.1.1/32 eq 443
   20 deny ip any any
!
end
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
        assert "ACL-TEST" in names
        assert "ACL-EXT" in names

    def test_acl_types(self):
        """Test ACL types are correctly identified."""
        acl_test = next(a for a in self.parsed.device.acls if a.name == "ACL-TEST")
        acl_ext = next(a for a in self.parsed.device.acls if a.name == "ACL-EXT")
        assert acl_test.type == ACLType.IPV4_EXTENDED
        assert acl_ext.type == ACLType.IPV4_EXTENDED

    def test_acl_test_entries(self):
        """Test ACL-TEST entries."""
        acl = next(a for a in self.parsed.device.acls if a.name == "ACL-TEST")
        assert len(acl.entries) == 2

    def test_acl_test_permit_entry(self):
        """Test ACL-TEST permit entry."""
        acl = next(a for a in self.parsed.device.acls if a.name == "ACL-TEST")
        entry = next(e for e in acl.entries if e.sequence == 10)
        assert entry.action == ACLAction.PERMIT
        assert entry.source == "192.168.1.0/24"
        assert entry.destination == "10.0.0.0/8"

    def test_acl_test_deny_entry(self):
        """Test ACL-TEST deny entry."""
        acl = next(a for a in self.parsed.device.acls if a.name == "ACL-TEST")
        entry = next(e for e in acl.entries if e.sequence == 20)
        assert entry.action == ACLAction.DENY
        assert entry.protocol == "tcp"
        assert entry.source == "172.16.0.0/16"
        assert "eq 23" in entry.destination

    def test_acl_ext_entries(self):
        """Test ACL-EXT entries."""
        acl = next(a for a in self.parsed.device.acls if a.name == "ACL-EXT")
        assert len(acl.entries) == 2

    def test_acl_ext_tcp_entry(self):
        """Test ACL-EXT TCP entry."""
        acl = next(a for a in self.parsed.device.acls if a.name == "ACL-EXT")
        entry = next(e for e in acl.entries if e.sequence == 10)
        assert entry.action == ACLAction.PERMIT
        assert entry.protocol == "tcp"
        assert entry.source == "10.0.0.1/32"
        assert "eq 443" in entry.destination


class TestAristaVXLAN:
    """Test VXLAN parsing capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = AristaEOSParser()
        self.config = """
! EOS version 4.28.3M
hostname LEAF-01
!
interface Vxlan1
   description VXLAN Interface
   vxlan source-interface Loopback0
   vxlan vlan 10 vni 10010
   vxlan vlan 20 vni 10020
   vxlan vlan 30 vni 10030
!
end
"""
        self.parsed = None

    @pytest.fixture(autouse=True)
    def parse_config(self):
        """Parse config once for all tests."""
        import asyncio
        async def parse():
            return await self.parser.parse(self.config)
        self.parsed = asyncio.run(parse())

    def test_vxlan_mappings_count(self):
        """Test correct number of VXLAN mappings."""
        assert len(self.parsed.device.vxlan_vni_mappings) == 3

    def test_vxlan_mapping_10(self):
        """Test VXLAN mapping for VLAN 10."""
        assert self.parsed.device.vxlan_vni_mappings[10] == 10010

    def test_vxlan_mapping_20(self):
        """Test VXLAN mapping for VLAN 20."""
        assert self.parsed.device.vxlan_vni_mappings[20] == 10020

    def test_vxlan_mapping_30(self):
        """Test VXLAN mapping for VLAN 30."""
        assert self.parsed.device.vxlan_vni_mappings[30] == 10030


class TestAristaUtilities:
    """Test utility functions."""

    def test_normalize_interface_name(self):
        """Test interface name normalization."""
        parser = AristaEOSParser()
        # Test various interface name formats
        assert parser._normalize_interface_name("Ethernet1") == "et1"
        assert parser._normalize_interface_name("Ethernet1/1") == "et1/1"
        assert parser._normalize_interface_name("Vlan10") == "vl10"
        assert parser._normalize_interface_name("Port-Channel1") == "po1"
        assert parser._normalize_interface_name("Loopback0") == "lo0"
        assert parser._normalize_interface_name("Management0") == "ma0"
        assert parser._normalize_interface_name("Vxlan1") == "vx1"

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
    """Minimal Arista config for edge case testing."""
    return """
! EOS version 4.28.3M
hostname MINIMAL
!
interface Ethernet1
   description Test
!
end
"""


@pytest.fixture
def full_config():
    """Full Arista config with all features for comprehensive testing."""
    return """
! EOS version 4.28.3M
! Model: DCS-7050CX3-32S
! Serial Number: SSJ18150206
hostname FULL-TEST-SWITCH
!
interface Ethernet1
   description Uplink to SPINE-01
   switchport mode trunk
   switchport trunk allowed vlan 10,20,30,40-50
   switchport trunk native vlan 1
   mtu 9216
   speed 10g
   duplex full
!
interface Ethernet2
   description Access Port
   switchport mode access
   switchport access vlan 100
!
interface Vlan10
   description Management SVI
   ip address 192.168.10.1/24
!
interface Vlan20
   description User SVI
   ip address 192.168.20.1/24
   vrf forwarding PROD
!
interface Loopback0
   description Router ID Loopback
   ip address 10.0.0.1/32
!
interface Port-Channel1
   description LACP Port Channel
!
interface Vxlan1
   description VXLAN Interface
   vxlan source-interface Loopback0
   vxlan vlan 10 vni 10010
   vxlan vlan 20 vni 10020
   vxlan vlan 30 vni 10030
!
vlan 10
   name USERS
   state active
!
vlan 20
   name SERVERS
!
vlan 30
   name GUESTS
   state suspend
!
vlan 100
   name ACCESS_VLAN
!
ip route 0.0.0.0/0 192.168.1.254
ip route 10.0.0.0/16 10.1.1.1 150
ip route vrf PROD 172.16.0.0/24 172.16.1.1
!
router ospf 100
   router-id 10.0.0.1
   network 192.168.10.0/24 area 0.0.0.0
   network 192.168.20.0/24 area 0.0.0.0
   redistribute static metric 10 metric-type 1
   redistribute connected metric 20 metric-type 2
!
router bgp 65001
   router-id 10.0.0.1
   neighbor 10.0.0.100 remote-as 65000
   neighbor 10.0.0.100 description SPINE-RR
   neighbor 10.0.0.200 remote-as 65002
   neighbor 10.0.0.200 peer group LEAF
   neighbor 10.0.0.201 remote-as 65002
   network 192.168.0.0/16
   network 10.0.0.0/24
!
vrf instance PROD
   rd 65001:100
!
vrf instance MGMT
   rd 65001:999
!
ip access-list ACL-TEST
   10 permit ip 192.168.1.0/24 10.0.0.0/8
   20 deny tcp 172.16.0.0/16 192.168.0.0/16 eq 23
   30 permit udp 10.0.0.1/32 192.168.1.1/32 eq 53
!
ip access-list extended ACL-EXT
   10 permit tcp 10.0.0.1/32 192.168.1.1/32 eq 443
   20 permit tcp 10.0.0.1/32 192.168.1.1/32 eq 80
   30 deny ip any any
!
end
"""

MINIMAL_EOS_CONFIG = """\
! EOS version 4.27.3F
hostname ARISTA-01
!
interface Ethernet1
   description WAN Link
   ip address 203.0.113.1/24
!
interface Ethernet2
   description LAN
   ip address 192.168.1.1/24
!
interface Loopback0
   ip address 10.0.0.1/32
!
end
"""

EOS_CONFIG_WITH_VLANS = """\
! device: ARISTA-SW (DCS-7280R, EOS-4.27.3F)
!
hostname ARISTA-SW
!
vlan 10
   name MANAGEMENT
!
vlan 20
   name DATA
!
vlan 30
   name VOICE
!
interface Ethernet1
   description Trunk to Core
   switchport mode trunk
   switchport trunk allowed vlan 10,20,30
!
interface Ethernet2
   description Access Port
   switchport mode access
   switchport access vlan 10
!
end
"""

EOS_CONFIG_WITH_ROUTING = """\
! device: ARISTA-RTR (DCS-7280R, EOS-4.27.3F)
!
hostname ARISTA-RTR
!
ip route 0.0.0.0/0 203.0.113.254
ip route 192.168.2.0/24 10.0.0.2
!
router ospf 1
   router-id 10.0.0.1
   network 10.0.0.0/8 area 0.0.0.0
   network 192.168.1.0/24 area 0.0.0.0
!
router bgp 65001
   router-id 10.0.0.1
   neighbor 10.0.0.2 remote-as 65002
   neighbor 10.0.0.2 description Upstream Provider
!
end
"""

EOS_CONFIG_WITH_ACL = """\
! device: ARISTA-FW (DCS-7280R, EOS-4.27.3F)
!
hostname ARISTA-FW
!
ip access-list INBOUND
   10 permit ip 192.168.1.0/24 any
   20 deny ip any any
!
interface Ethernet1
   description Outside
   ip address 203.0.113.1/24
   ip access-group INBOUND in
!
end
"""

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAristaEOSParser:
    """Test Arista EOS parser functionality."""

    @pytest.fixture
    def parser(self) -> AristaEOSParser:
        """Return a fresh parser instance."""
        return AristaEOSParser()

    # ------------------------------------------------------------------
    # Vendor detection tests
    # ------------------------------------------------------------------

    def test_can_parse_minimal_config(self, parser: AristaEOSParser):
        """Test detection of minimal Arista EOS config."""
        assert parser.can_parse(MINIMAL_EOS_CONFIG)

    def test_can_parse_with_vlans(self, parser: AristaEOSParser):
        """Test detection of EOS config with VLANs."""
        assert parser.can_parse(EOS_CONFIG_WITH_VLANS)

    def test_cannot_parse_empty_config(self, parser: AristaEOSParser):
        """Test rejection of empty config."""
        assert not parser.can_parse("")
        assert not parser.can_parse("   \n\t  ")

    def test_cannot_parse_cisco_config(self, parser: AristaEOSParser):
        """Test rejection of Cisco IOS config."""
        cisco_config = "hostname ROUTER-01\ninterface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0"
        assert not parser.can_parse(cisco_config)

    # ------------------------------------------------------------------
    # Basic parsing tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_parse_minimal_config(self, parser: AristaEOSParser):
        """Test parsing of minimal EOS config."""
        result = await parser.parse(MINIMAL_EOS_CONFIG)

        assert result.device.hostname == "ARISTA-01"
        assert result.device.vendor == VendorType.ARISTA_EOS
        assert "4.27.3" in result.device.os_version
        assert len(result.device.interfaces) == 3

        # Check interfaces
        eth1 = next(iface for iface in result.device.interfaces if iface.name == "Ethernet1")
        assert eth1.description == "WAN Link"
        assert eth1.ipv4_addresses == ["203.0.113.1/24"]
        assert eth1.enabled is True

        eth2 = next(iface for iface in result.device.interfaces if iface.name == "Ethernet2")
        assert eth2.description == "LAN"
        assert eth2.ipv4_addresses == ["192.168.1.1/24"]

        lo0 = next(iface for iface in result.device.interfaces if iface.name == "Loopback0")
        assert lo0.ipv4_addresses == ["10.0.0.1/32"]

    @pytest.mark.asyncio
    async def test_parse_vlan_config(self, parser: AristaEOSParser):
        """Test parsing of VLAN configuration."""
        result = await parser.parse(EOS_CONFIG_WITH_VLANS)

        assert result.device.hostname == "ARISTA-SW"
        assert len(result.device.vlans) == 3

        # Check VLANs
        vlan10 = next(vlan for vlan in result.device.vlans if vlan.id == 10)
        assert vlan10.name == "MANAGEMENT"

        vlan20 = next(vlan for vlan in result.device.vlans if vlan.id == 20)
        assert vlan20.name == "DATA"

        vlan30 = next(vlan for vlan in result.device.vlans if vlan.id == 30)
        assert vlan30.name == "VOICE"

        # Check interfaces
        trunk_iface = next(iface for iface in result.device.interfaces if iface.name == "Ethernet1")
        assert trunk_iface.mode == SwitchportMode.TRUNK
        assert trunk_iface.trunk_allowed_vlans == [10, 20, 30]

        access_iface = next(iface for iface in result.device.interfaces if iface.name == "Ethernet2")
        assert access_iface.mode == SwitchportMode.ACCESS
        assert access_iface.access_vlan == 10

    @pytest.mark.asyncio
    async def test_parse_routing_config(self, parser: AristaEOSParser):
        """Test parsing of routing configuration."""
        result = await parser.parse(EOS_CONFIG_WITH_ROUTING)

        assert result.device.hostname == "ARISTA-RTR"

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
        assert bgp.neighbors[0].description == "Upstream Provider"

    @pytest.mark.asyncio
    async def test_parse_acl_config(self, parser: AristaEOSParser):
        """Test parsing of ACL configuration."""
        result = await parser.parse(EOS_CONFIG_WITH_ACL)

        assert result.device.hostname == "ARISTA-FW"

        # Check ACLs
        assert len(result.device.acls) == 1
        acl = result.device.acls[0]
        assert acl.name == "INBOUND"
        assert acl.type == ACLType.IPV4_EXTENDED
        assert len(acl.entries) == 2

        permit_rule = next(entry for entry in acl.entries if entry.sequence == 10)
        assert permit_rule.action == ACLAction.PERMIT

        deny_rule = next(entry for entry in acl.entries if entry.sequence == 20)
        assert deny_rule.action == ACLAction.DENY

    # ------------------------------------------------------------------
    # Error handling tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_parse_empty_config_raises_error(self, parser: AristaEOSParser):
        """Test that empty config raises ParserError."""
        with pytest.raises(ParserError, match="Configuration is empty"):
            await parser.parse("")

    @pytest.mark.asyncio
    async def test_parse_invalid_config_graceful_handling(self, parser: AristaEOSParser):
        """Test graceful handling of invalid config sections."""
        invalid_config = """\
! device: TEST (DCS-7280R, EOS-4.27.3F)
!
hostname TEST
!
interface Ethernet1
   invalid command that should be ignored
   ip address 192.168.1.1/24
!
end
"""
        result = await parser.parse(invalid_config)
        assert result.device.hostname == "TEST"
        assert len(result.device.interfaces) == 1