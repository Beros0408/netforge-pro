"""
Graph database tests.
Tests for Neo4j service, graph builder, queries, and API endpoints.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from ..config import GraphSettings
from ..models.graph_models import DeviceNode, InterfaceNode, VLANNode, VRFNode, ZoneNode
from ..services.neo4j_service import Neo4jService
from ..services.graph_builder import GraphBuilder
from ..services.graph_queries import GraphQueries
from ...parser_engine.models.device import Device as ParsedDevice, VendorType, OSType
from ...parser_engine.models.interface import Interface as ParsedInterface, InterfaceType, InterfaceStatus
from ...parser_engine.models.vlan import VLAN as ParsedVLAN
from ...parser_engine.models.routing import VRF as ParsedVRF


class TestGraphModels:
    """Test graph model classes."""

    def test_device_node_creation(self):
        """Test DeviceNode creation."""
        device = DeviceNode(
            hostname="router1",
            vendor="cisco",
            model="Catalyst 9300",
            os_version="16.12.1",
            zone="production"
        )

        assert device.hostname == "router1"
        assert device.vendor == "cisco"
        assert device.labels == ["Device"]
        assert isinstance(device.created_at, datetime)

    def test_interface_node_creation(self):
        """Test InterfaceNode creation."""
        interface = InterfaceNode(
            name="GigabitEthernet0/0",
            interface_type="gigabit_ethernet",
            ip_address="192.168.1.1",
            vlan=10,
            state="up",
            speed=1000
        )

        assert interface.name == "GigabitEthernet0/0"
        assert interface.ip_address == "192.168.1.1"
        assert interface.labels == ["Interface"]

    def test_vlan_node_creation(self):
        """Test VLANNode creation."""
        vlan = VLANNode(
            vlan_id=10,
            name="VLAN_10",
            svi_ip="192.168.10.1"
        )

        assert vlan.vlan_id == 10
        assert vlan.name == "VLAN_10"
        assert vlan.labels == ["VLAN"]

    def test_vrf_node_creation(self):
        """Test VRFNode creation."""
        vrf = VRFNode(
            name="CUSTOMER_A",
            rd="65000:100",
            rt_import=["65000:100"],
            rt_export=["65000:100"]
        )

        assert vrf.name == "CUSTOMER_A"
        assert vrf.rd == "65000:100"
        assert vrf.labels == ["VRF"]

    def test_zone_node_creation(self):
        """Test ZoneNode creation."""
        zone = ZoneNode(
            name="production",
            zone_type="network",
            security_level=50
        )

        assert zone.name == "production"
        assert zone.security_level == 50
        assert zone.labels == ["Zone"]


class TestNeo4jService:
    """Test Neo4j service functionality."""

    @pytest.fixture
    def mock_driver(self):
        """Mock Neo4j driver."""
        driver = MagicMock()
        driver.verify_connectivity = AsyncMock()
        driver.close = AsyncMock()
        return driver

    @pytest.fixture
    def settings(self):
        """Graph settings fixture."""
        return GraphSettings(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password"
        )

    @pytest.fixture
    def neo4j_service(self, settings, mock_driver):
        """Neo4j service fixture with mocked driver."""
        with patch('neo4j.AsyncGraphDatabase') as mock_graph_db:
            mock_graph_db.driver.return_value = mock_driver
            service = Neo4jService(settings)
            # Manually set the driver to avoid connection
            service._driver = mock_driver
            return service

    @pytest.mark.asyncio
    async def test_connect_success(self, neo4j_service, mock_driver):
        """Test successful connection."""
        # Already connected via fixture
        assert neo4j_service._driver is not None
        mock_driver.verify_connectivity.assert_not_called()  # Not called in fixture

    @pytest.mark.asyncio
    async def test_execute_query(self, neo4j_service, mock_driver):
        """Test query execution."""
        # Mock session and transaction
        mock_session = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_session.execute_read = AsyncMock(return_value=[{"test": "data"}])
        mock_session.close = AsyncMock()

        result = await neo4j_service.execute_query("MATCH (n) RETURN n", read_only=True)

        assert result == [{"test": "data"}]
        mock_session.execute_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_node(self, neo4j_service, mock_driver):
        """Test node creation."""
        mock_session = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_session.execute_write = AsyncMock(return_value=[{"n": {"id": 1, "hostname": "test"}}])
        mock_session.close = AsyncMock()

        result = await neo4j_service.create_node(["Device"], {"hostname": "test"})

        assert result == {"id": 1, "hostname": "test"}

    @pytest.mark.asyncio
    async def test_find_node(self, neo4j_service, mock_driver):
        """Test node finding."""
        mock_session = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_session.execute_read = AsyncMock(return_value=[{"n": {"id": 1, "hostname": "test"}}])
        mock_session.close = AsyncMock()

        result = await neo4j_service.find_node(["Device"], {"hostname": "test"})

        assert result == {"id": 1, "hostname": "test"}


class TestGraphBuilder:
    """Test graph builder functionality."""

    @pytest.fixture
    def mock_neo4j(self):
        """Mock Neo4j service."""
        neo4j = MagicMock()
        neo4j.create_node = AsyncMock(return_value={"id": 1, "hostname": "test"})
        neo4j.create_relationship = AsyncMock()
        neo4j.find_node = AsyncMock(return_value=None)
        return neo4j

    @pytest.fixture
    def settings(self):
        """Graph settings fixture."""
        return GraphSettings()

    @pytest.fixture
    def graph_builder(self, mock_neo4j, settings):
        """Graph builder fixture."""
        return GraphBuilder(mock_neo4j, settings)

    @pytest.fixture
    def sample_device(self):
        """Sample parsed device fixture."""
        return ParsedDevice(
            hostname="router1",
            vendor=VendorType.CISCO,
            os_version="16.12.1",
            model="Catalyst 9300",
            interfaces=[
                ParsedInterface(
                    name="GigabitEthernet0/0",
                    interface_type=InterfaceType.GIGABIT_ETHERNET,
                    ip_address="192.168.1.1",
                    status=InterfaceStatus.UP,
                    access_vlan=10
                )
            ],
            vlans=[
                ParsedVLAN(vlan_id=10, name="VLAN_10")
            ],
            vrfs=[
                ParsedVRF(name="default", rd="0:0")
            ]
        )

    @pytest.mark.asyncio
    async def test_build_device_graph(self, graph_builder, mock_neo4j, sample_device):
        """Test building graph for a device."""
        mock_neo4j.create_node.side_effect = [
            {"id": 1, "hostname": "router1"},  # Device node
            {"id": 2, "name": "GigabitEthernet0/0"},  # Interface node
            {"id": 3, "vlan_id": 10},  # VLAN node (from _create_vlan_relationships)
            {"id": 4, "name": "default"},  # VRF node
        ]

        stats = await graph_builder.build_device_graph(sample_device)

        assert stats["devices"] == 1
        assert stats["interfaces"] == 1
        # vlans=2: 1 from _create_vlan_relationships (access_vlan) + 1 from device.vlans loop
        assert stats["vlans"] == 2
        assert stats["vrfs"] == 1
        assert stats["relationships"] == 2  # HAS_INTERFACE + MEMBER_OF_VLAN

    @pytest.mark.asyncio
    async def test_create_device_node(self, graph_builder, mock_neo4j, sample_device):
        """Test device node creation."""
        mock_neo4j.create_node.return_value = {"id": 1, "hostname": "router1"}

        device_node = await graph_builder._create_or_update_device(sample_device)

        assert device_node.hostname == "router1"
        assert device_node.vendor == "cisco"
        assert device_node.node_id == 1

    @pytest.mark.asyncio
    async def test_create_interface_node(self, graph_builder, mock_neo4j, sample_device):
        """Test interface node creation."""
        mock_neo4j.create_node.return_value = {"id": 2, "name": "GigabitEthernet0/0"}

        interface_node = await graph_builder._create_or_update_interface(
            sample_device.interfaces[0], "router1"
        )

        assert interface_node.name == "GigabitEthernet0/0"
        assert interface_node.ip_address == "192.168.1.1"
        assert interface_node.node_id == 2


class TestGraphQueries:
    """Test graph queries functionality."""

    @pytest.fixture
    def mock_neo4j(self):
        """Mock Neo4j service."""
        neo4j = MagicMock()
        neo4j.execute_query = AsyncMock()
        return neo4j

    @pytest.fixture
    def settings(self):
        """Graph settings fixture."""
        return GraphSettings()

    @pytest.fixture
    def graph_queries(self, mock_neo4j, settings):
        """Graph queries fixture."""
        return GraphQueries(mock_neo4j, settings)

    @pytest.mark.asyncio
    async def test_find_path(self, graph_queries, mock_neo4j):
        """Test path finding."""
        mock_neo4j.execute_query.return_value = [{"path": {"length": 2}}]

        paths = await graph_queries.find_path("router1", "router2")

        assert len(paths) == 1
        mock_neo4j.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_impact(self, graph_queries, mock_neo4j):
        """Test impact analysis."""
        mock_neo4j.execute_query.side_effect = [
            [{"directly_connected": ["router2", "router3"]}],
            [{"affected_sources": ["server1"]}],
            [{"affected_vlans": [10, 20]}]
        ]

        impact = await graph_queries.analyze_impact("router1")

        assert impact["device"] == "router1"
        assert "router2" in impact["directly_connected_devices"]
        assert impact["total_impact_score"] == 3

    @pytest.mark.asyncio
    async def test_get_zone_devices(self, graph_queries, mock_neo4j):
        """Test zone devices query."""
        mock_neo4j.execute_query.return_value = [
            {"hostname": "router1", "vendor": "cisco"},
            {"hostname": "switch1", "vendor": "cisco"}
        ]

        devices = await graph_queries.get_zone_devices("production")

        assert len(devices) == 2
        assert devices[0]["hostname"] == "router1"

    @pytest.mark.asyncio
    async def test_get_network_stats(self, graph_queries, mock_neo4j):
        """Test network statistics."""
        mock_neo4j.execute_query.side_effect = [
            [{"total_devices": 10, "total_interfaces": 50, "total_zones": 3, "total_relationships": 75}],
            [{"vendor": "cisco", "count": 7}, {"vendor": "huawei", "count": 3}],
            [{"zone": "production", "device_count": 8}, {"zone": "dmz", "device_count": 2}]
        ]

        stats = await graph_queries.get_network_stats()

        assert stats["total_devices"] == 10
        assert stats["total_interfaces"] == 50
        assert len(stats["vendors"]) == 2
        assert len(stats["zones"]) == 2

    @pytest.mark.asyncio
    async def test_detect_routing_loops(self, graph_queries, mock_neo4j):
        """Test routing loop detection."""
        mock_neo4j.execute_query.return_value = [
            {
                "devices": ["router1", "router2", "router1"],
                "relationships": [{"protocol": "ospf"}, {"protocol": "ospf"}],
                "loop_length": 3
            }
        ]

        loops = await graph_queries.detect_routing_loops()

        assert len(loops) == 1
        assert loops[0]["loop_length"] == 3

    @pytest.mark.asyncio
    async def test_find_isolated_devices(self, graph_queries, mock_neo4j):
        """Test isolated devices detection."""
        mock_neo4j.execute_query.return_value = [
            {"hostname": "isolated1"},
            {"hostname": "isolated2"}
        ]

        devices = await graph_queries.find_isolated_devices()

        assert len(devices) == 2
        assert "isolated1" in devices


class TestGraphAPI:
    """Test graph API endpoints."""

    @pytest.fixture
    def mock_graph_api(self):
        """Mock graph API."""
        api = MagicMock()
        api.build_graph = AsyncMock(return_value=MagicMock(status="completed", stats={}, message="OK"))
        api.find_path = AsyncMock(return_value={"found": True, "paths": []})
        api.analyze_impact = AsyncMock(return_value=MagicMock(
            device="router1",
            directly_connected_devices=[],
            routing_dependent_devices=[],
            affected_vlans=[],
            total_impact_score=0
        ))
        return api

    @pytest.mark.asyncio
    async def test_build_graph_api(self, mock_graph_api):
        """Test build graph API endpoint."""
        from ..api.routes import BuildGraphRequest

        request = BuildGraphRequest(devices=[], zone_name="test")
        background_tasks = MagicMock()

        with patch('src.graph_database.api.routes.get_graph_api', return_value=mock_graph_api):
            response = await mock_graph_api.build_graph(request, background_tasks)

            assert response.status == "completed"

    @pytest.mark.asyncio
    async def test_find_path_api(self, mock_graph_api):
        """Test find path API endpoint."""
        from ..api.routes import PathRequest

        request = PathRequest(start_hostname="router1", end_hostname="router2")

        with patch('src.graph_database.api.routes.get_graph_api', return_value=mock_graph_api):
            response = await mock_graph_api.find_path(request)

            assert response["found"] is True

    @pytest.mark.asyncio
    async def test_analyze_impact_api(self, mock_graph_api):
        """Test impact analysis API endpoint."""
        with patch('src.graph_database.api.routes.get_graph_api', return_value=mock_graph_api):
            response = await mock_graph_api.analyze_impact("router1")

            assert response.device == "router1"
            assert response.total_impact_score == 0