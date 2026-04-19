"""
Graph database API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..config import GraphSettings
from ..services.graph_builder import GraphBuilder
from ..services.graph_queries import GraphQueries
from ..services.neo4j_service import Neo4jService
from ...parser_engine.models.device import Device as ParsedDevice

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


# Pydantic models for API requests/responses
class BuildGraphRequest(BaseModel):
    """Request model for building graph from devices."""
    devices: List[ParsedDevice] = Field(..., description="List of parsed devices")
    zone_name: Optional[str] = Field(None, description="Zone to place devices in")


class BuildGraphResponse(BaseModel):
    """Response model for graph building operation."""
    status: str = Field(..., description="Operation status")
    stats: dict = Field(..., description="Build statistics")
    message: str = Field(..., description="Status message")


class PathRequest(BaseModel):
    """Request model for path finding."""
    start_hostname: str = Field(..., description="Starting device hostname")
    end_hostname: str = Field(..., description="Ending device hostname")
    max_length: Optional[int] = Field(10, description="Maximum path length")


class ImpactResponse(BaseModel):
    """Response model for impact analysis."""
    device: str = Field(..., description="Analyzed device")
    directly_connected_devices: List[str] = Field(..., description="Directly connected devices")
    routing_dependent_devices: List[str] = Field(..., description="Devices routing through this one")
    affected_vlans: List[int] = Field(..., description="Affected VLANs")
    total_impact_score: int = Field(..., description="Total impact score")


class NetworkStatsResponse(BaseModel):
    """Response model for network statistics."""
    total_devices: int = Field(..., description="Total number of devices")
    total_interfaces: int = Field(..., description="Total number of interfaces")
    total_zones: int = Field(..., description="Total number of zones")
    total_relationships: int = Field(..., description="Total number of relationships")
    vendors: List[dict] = Field(..., description="Device count by vendor")
    zones: List[dict] = Field(..., description="Device count by zone")


class GraphAPI:
    """
    Graph database API endpoints.

    Provides REST API for graph operations including building, querying,
    and analysis of network topology.
    """

    def __init__(self, neo4j_service: Neo4jService, graph_builder: GraphBuilder, graph_queries: GraphQueries, settings: GraphSettings):
        """
        Initialize graph API.

        Args:
            neo4j_service: Neo4j service instance
            graph_builder: Graph builder service
            graph_queries: Graph queries service
            settings: Graph settings
        """
        self.neo4j = neo4j_service
        self.builder = graph_builder
        self.queries = graph_queries
        self.settings = settings

    async def build_graph(self, request: BuildGraphRequest, background_tasks: BackgroundTasks) -> BuildGraphResponse:
        """
        Build graph from parsed devices.

        Args:
            request: Build graph request
            background_tasks: FastAPI background tasks

        Returns:
            Build operation response
        """
        try:
            # For large builds, run in background
            if len(request.devices) > self.settings.graph_batch_size:
                background_tasks.add_task(
                    self._build_graph_background,
                    request.devices,
                    request.zone_name
                )
                return BuildGraphResponse(
                    status="running",
                    stats={},
                    message=f"Graph build started for {len(request.devices)} devices in background"
                )
            else:
                # Build synchronously
                stats = await self.builder.build_devices_batch(request.devices, request.zone_name)
                return BuildGraphResponse(
                    status="completed",
                    stats=stats,
                    message=f"Graph built successfully with {stats['devices']} devices"
                )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Graph build failed: {str(e)}")

    async def _build_graph_background(self, devices: List[ParsedDevice], zone_name: Optional[str]) -> None:
        """
        Background task for building large graphs.

        Args:
            devices: List of devices to build
            zone_name: Optional zone name
        """
        try:
            stats = await self.builder.build_devices_batch(devices, zone_name)
            # In a real implementation, you might want to store the result
            # or send a notification when complete
        except Exception as e:
            # Log the error - in production you'd want proper error handling
            pass

    async def find_path(self, request: PathRequest) -> dict:
        """
        Find path between two devices.

        Args:
            request: Path finding request

        Returns:
            Path information
        """
        try:
            paths = await self.queries.find_path(
                request.start_hostname,
                request.end_hostname,
                request.max_length
            )

            if not paths:
                return {
                    "found": False,
                    "message": f"No path found between {request.start_hostname} and {request.end_hostname}"
                }

            return {
                "found": True,
                "paths": paths,
                "message": f"Found {len(paths)} path(s)"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Path finding failed: {str(e)}")

    async def analyze_impact(self, hostname: str) -> ImpactResponse:
        """
        Analyze impact of device failure.

        Args:
            hostname: Device hostname

        Returns:
            Impact analysis
        """
        try:
            impact = await self.queries.analyze_impact(hostname)
            return ImpactResponse(**impact)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Impact analysis failed: {str(e)}")

    async def get_zone_devices(self, zone_name: str) -> List[dict]:
        """
        Get all devices in a zone.

        Args:
            zone_name: Zone name

        Returns:
            List of devices
        """
        try:
            devices = await self.queries.get_zone_devices(zone_name)
            return devices

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Zone query failed: {str(e)}")

    async def get_trunk_vlans(self, device_hostname: str, interface_name: str) -> List[dict]:
        """
        Get VLANs on a trunk interface.

        Args:
            device_hostname: Device hostname
            interface_name: Interface name

        Returns:
            List of VLANs
        """
        try:
            vlans = await self.queries.get_trunk_vlans(interface_name, device_hostname)
            return vlans

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Trunk VLAN query failed: {str(e)}")

    async def detect_loops(self) -> List[dict]:
        """
        Detect routing loops.

        Returns:
            List of detected loops
        """
        try:
            loops = await self.queries.detect_routing_loops()
            return loops

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Loop detection failed: {str(e)}")

    async def get_network_stats(self) -> NetworkStatsResponse:
        """
        Get network statistics.

        Returns:
            Network statistics
        """
        try:
            stats = await self.queries.get_network_stats()
            return NetworkStatsResponse(**stats)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")

    async def get_device_topology(self, hostname: str, depth: int = 2) -> dict:
        """
        Get device topology.

        Args:
            hostname: Device hostname
            depth: Topology depth

        Returns:
            Device topology information
        """
        try:
            topology = await self.queries.get_device_topology(hostname, depth)
            return topology

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Topology query failed: {str(e)}")

    async def find_isolated_devices(self) -> List[str]:
        """
        Find isolated devices.

        Returns:
            List of isolated device hostnames
        """
        try:
            devices = await self.queries.find_isolated_devices()
            return devices

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Isolated devices query failed: {str(e)}")

    async def clear_database(self) -> dict:
        """
        Clear all graph data.

        Returns:
            Operation result
        """
        try:
            await self.neo4j.clear_database()
            self.builder.clear_cache()
            return {
                "status": "cleared",
                "message": "Graph database cleared successfully"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database clear failed: {str(e)}")


# Global API instance (would be initialized in main app)
graph_api = None

def get_graph_api() -> GraphAPI:
    """Get the global graph API instance."""
    if graph_api is None:
        raise RuntimeError("Graph API not initialized")
    return graph_api

def init_graph_api(neo4j_service: Neo4jService, graph_builder: GraphBuilder, graph_queries: GraphQueries, settings: GraphSettings):
    """Initialize the global graph API instance."""
    global graph_api
    graph_api = GraphAPI(neo4j_service, graph_builder, graph_queries, settings)


# API Routes
@router.post("/build", response_model=BuildGraphResponse)
async def build_graph(request: BuildGraphRequest, background_tasks: BackgroundTasks):
    """Build graph from parsed devices."""
    return await get_graph_api().build_graph(request, background_tasks)

@router.post("/path", response_model=dict)
async def find_path(request: PathRequest):
    """Find path between two devices."""
    return await get_graph_api().find_path(request)

@router.get("/impact/{hostname}", response_model=ImpactResponse)
async def analyze_impact(hostname: str):
    """Analyze impact of device failure."""
    return await get_graph_api().analyze_impact(hostname)

@router.get("/zone/{zone_name}/devices", response_model=List[dict])
async def get_zone_devices(zone_name: str):
    """Get all devices in a zone."""
    return await get_graph_api().get_zone_devices(zone_name)

@router.get("/device/{device_hostname}/interface/{interface_name}/vlans", response_model=List[dict])
async def get_trunk_vlans(device_hostname: str, interface_name: str):
    """Get VLANs on a trunk interface."""
    return await get_graph_api().get_trunk_vlans(device_hostname, interface_name)

@router.get("/loops", response_model=List[dict])
async def detect_loops():
    """Detect routing loops."""
    return await get_graph_api().detect_loops()

@router.get("/stats", response_model=NetworkStatsResponse)
async def get_network_stats():
    """Get network statistics."""
    return await get_graph_api().get_network_stats()

@router.get("/device/{hostname}/topology", response_model=dict)
async def get_device_topology(hostname: str, depth: int = 2):
    """Get device topology."""
    return await get_graph_api().get_device_topology(hostname, depth)

@router.get("/isolated", response_model=List[str])
async def find_isolated_devices():
    """Find isolated devices."""
    return await get_graph_api().find_isolated_devices()

@router.delete("/clear")
async def clear_database():
    """Clear all graph data (DANGER!)."""
    return await get_graph_api().clear_database()