"""
Graph queries service.
Provides Cypher queries for network topology analysis and path finding.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

from ..config import GraphSettings
from .neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


class GraphQueries:
    """
    Service for executing complex graph queries on network topology.

    Provides methods for path finding, impact analysis, loop detection,
    and various network topology queries.
    """

    def __init__(self, neo4j_service: Neo4jService, settings: GraphSettings):
        """
        Initialize graph queries service.

        Args:
            neo4j_service: Neo4j service instance
            settings: Graph database settings
        """
        self.neo4j = neo4j_service
        self.settings = settings

    async def find_path(self, start_hostname: str, end_hostname: str, max_length: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Find shortest path between two devices.

        Args:
            start_hostname: Starting device hostname
            end_hostname: Ending device hostname
            max_length: Maximum path length

        Returns:
            List of path segments with device and relationship data
        """
        max_length = max_length or self.settings.graph_max_path_length

        query = """
        MATCH path = shortestPath(
            (start:Device {hostname: $start_hostname})-[*1..{max_length}]->(end:Device {hostname: $end_hostname})
        )
        RETURN path
        """

        try:
            result = await self.neo4j.execute_query(
                query,
                {"start_hostname": start_hostname, "end_hostname": end_hostname, "max_length": max_length},
                read_only=True
            )

            if not result:
                return []

            # Process path data
            paths = []
            for record in result:
                path_data = record.get("path", {})
                paths.append(self._process_path_data(path_data))

            return paths

        except Exception as e:
            logger.error(f"Failed to find path from {start_hostname} to {end_hostname}: {e}")
            return []

    async def detect_routing_loops(self) -> List[Dict[str, Any]]:
        """
        Detect routing loops in the network topology.

        Returns:
            List of detected loops with device information
        """
        query = """
        MATCH path = (d:Device)-[r:ROUTES_TO*]->(d:Device)
        WHERE length(path) > 2
        RETURN
            [node IN nodes(path) | node.hostname] as devices,
            [rel IN relationships(path) | {
                protocol: rel.protocol,
                metric: rel.metric,
                next_hop: rel.next_hop
            }] as relationships,
            length(path) as loop_length
        ORDER BY loop_length DESC
        LIMIT 50
        """

        try:
            result = await self.neo4j.execute_query(query, read_only=True)
            return [record for record in result]
        except Exception as e:
            logger.error(f"Failed to detect routing loops: {e}")
            return []

    async def get_zone_devices(self, zone_name: str) -> List[Dict[str, Any]]:
        """
        Get all devices in a specific zone.

        Args:
            zone_name: Zone name

        Returns:
            List of devices in the zone
        """
        query = """
        MATCH (d:Device)-[:LOCATED_IN]->(z:Zone {name: $zone_name})
        RETURN d.hostname as hostname,
               d.vendor as vendor,
               d.model as model,
               d.os_version as os_version
        ORDER BY d.hostname
        """

        try:
            result = await self.neo4j.execute_query(query, {"zone_name": zone_name}, read_only=True)
            return [record for record in result]
        except Exception as e:
            logger.error(f"Failed to get devices in zone {zone_name}: {e}")
            return []

    async def analyze_impact(self, device_hostname: str) -> Dict[str, Any]:
        """
        Analyze impact if a device goes down.

        Args:
            device_hostname: Device hostname to analyze

        Returns:
            Impact analysis with affected devices and services
        """
        # Find directly connected devices
        connected_query = """
        MATCH (target:Device {hostname: $hostname})<-[:CONNECTED_TO|ROUTES_TO]-(d:Device)
        RETURN collect(DISTINCT d.hostname) as directly_connected
        """

        # Find devices that route through this device
        routing_impact_query = """
        MATCH (source:Device)-[r:ROUTES_TO*]->(target:Device {hostname: $hostname})
        WHERE ALL(rel IN r WHERE rel.next_hop IS NOT NULL)
        RETURN collect(DISTINCT source.hostname) as affected_sources
        """

        # Find VLAN impact
        vlan_impact_query = """
        MATCH (target:Device {hostname: $hostname})-[:HAS_INTERFACE]->(i:Interface)-[:MEMBER_OF_VLAN]->(v:VLAN)
        RETURN collect(DISTINCT v.vlan_id) as affected_vlans
        """

        try:
            connected_result = await self.neo4j.execute_query(connected_query, {"hostname": device_hostname}, read_only=True)
            routing_result = await self.neo4j.execute_query(routing_impact_query, {"hostname": device_hostname}, read_only=True)
            vlan_result = await self.neo4j.execute_query(vlan_impact_query, {"hostname": device_hostname}, read_only=True)

            return {
                "device": device_hostname,
                "directly_connected_devices": connected_result[0]["directly_connected"] if connected_result else [],
                "routing_dependent_devices": routing_result[0]["affected_sources"] if routing_result else [],
                "affected_vlans": vlan_result[0]["affected_vlans"] if vlan_result else [],
                "total_impact_score": len(connected_result[0]["directly_connected"] if connected_result else []) +
                                    len(routing_result[0]["affected_sources"] if routing_result else [])
            }

        except Exception as e:
            logger.error(f"Failed to analyze impact for {device_hostname}: {e}")
            return {
                "device": device_hostname,
                "error": str(e),
                "directly_connected_devices": [],
                "routing_dependent_devices": [],
                "affected_vlans": [],
                "total_impact_score": 0
            }

    async def get_trunk_vlans(self, interface_name: str, device_hostname: str) -> List[Dict[str, Any]]:
        """
        Get all VLANs on a trunk interface.

        Args:
            interface_name: Interface name
            device_hostname: Device hostname

        Returns:
            List of VLANs on the trunk
        """
        query = """
        MATCH (d:Device {hostname: $device_hostname})-[:HAS_INTERFACE]->(i:Interface {name: $interface_name})-[r:MEMBER_OF_VLAN {mode: 'trunk'}]->(v:VLAN)
        RETURN v.vlan_id as vlan_id,
               v.name as vlan_name,
               r.native as is_native
        ORDER BY v.vlan_id
        """

        try:
            result = await self.neo4j.execute_query(
                query,
                {"interface_name": interface_name, "device_hostname": device_hostname},
                read_only=True
            )
            return [record for record in result]
        except Exception as e:
            logger.error(f"Failed to get trunk VLANs for {device_hostname}:{interface_name}: {e}")
            return []

    async def get_device_topology(self, device_hostname: str, depth: int = 2) -> Dict[str, Any]:
        """
        Get complete topology information for a device.

        Args:
            device_hostname: Device hostname
            depth: Relationship depth to explore

        Returns:
            Device topology with interfaces, connections, and routes
        """
        # Get device basic info
        device_query = """
        MATCH (d:Device {hostname: $hostname})
        RETURN d
        """

        # Get interfaces
        interfaces_query = """
        MATCH (d:Device {hostname: $hostname})-[:HAS_INTERFACE]->(i:Interface)
        RETURN i
        """

        # Get connections
        connections_query = """
        MATCH (d:Device {hostname: $hostname})-[:HAS_INTERFACE]->(i:Interface)-[c:CONNECTED_TO]-(remote_i:Interface)<-[:HAS_INTERFACE]-(remote_d:Device)
        RETURN i.name as local_interface,
               remote_d.hostname as remote_device,
               remote_i.name as remote_interface,
               c.speed as speed,
               c.status as status
        """

        # Get routes
        routes_query = """
        MATCH (d:Device {hostname: $hostname})-[r:ROUTES_TO]->(remote_d:Device)
        RETURN remote_d.hostname as target_device,
               r.protocol as protocol,
               r.metric as metric,
               r.network as network,
               r.next_hop as next_hop
        """

        try:
            device_result = await self.neo4j.execute_query(device_query, {"hostname": device_hostname}, read_only=True)
            interfaces_result = await self.neo4j.execute_query(interfaces_query, {"hostname": device_hostname}, read_only=True)
            connections_result = await self.neo4j.execute_query(connections_query, {"hostname": device_hostname}, read_only=True)
            routes_result = await self.neo4j.execute_query(routes_query, {"hostname": device_hostname}, read_only=True)

            return {
                "device": device_result[0]["d"] if device_result else None,
                "interfaces": [r["i"] for r in interfaces_result],
                "connections": [r for r in connections_result],
                "routes": [r for r in routes_result]
            }

        except Exception as e:
            logger.error(f"Failed to get topology for {device_hostname}: {e}")
            return {
                "device": None,
                "interfaces": [],
                "connections": [],
                "routes": [],
                "error": str(e)
            }

    async def get_network_stats(self) -> Dict[str, Any]:
        """
        Get overall network statistics.

        Returns:
            Network statistics
        """
        stats_query = """
        MATCH (d:Device)
        OPTIONAL MATCH (d)-[:HAS_INTERFACE]->(i:Interface)
        OPTIONAL MATCH (d)-[:LOCATED_IN]->(z:Zone)
        OPTIONAL MATCH (d)-[r:ROUTES_TO|CONNECTED_TO]->()
        RETURN
            count(DISTINCT d) as total_devices,
            count(DISTINCT i) as total_interfaces,
            count(DISTINCT z) as total_zones,
            count(DISTINCT r) as total_relationships
        """

        vendor_query = """
        MATCH (d:Device)
        RETURN d.vendor as vendor, count(d) as count
        ORDER BY count DESC
        """

        zone_query = """
        MATCH (d:Device)-[:LOCATED_IN]->(z:Zone)
        RETURN z.name as zone, count(d) as device_count
        ORDER BY device_count DESC
        """

        try:
            stats_result = await self.neo4j.execute_query(stats_query, read_only=True)
            vendor_result = await self.neo4j.execute_query(vendor_query, read_only=True)
            zone_result = await self.neo4j.execute_query(zone_query, read_only=True)

            stats = stats_result[0] if stats_result else {}

            return {
                "total_devices": stats.get("total_devices", 0),
                "total_interfaces": stats.get("total_interfaces", 0),
                "total_zones": stats.get("total_zones", 0),
                "total_relationships": stats.get("total_relationships", 0),
                "vendors": [r for r in vendor_result],
                "zones": [r for r in zone_result]
            }

        except Exception as e:
            logger.error(f"Failed to get network stats: {e}")
            return {
                "error": str(e),
                "total_devices": 0,
                "total_interfaces": 0,
                "total_zones": 0,
                "total_relationships": 0,
                "vendors": [],
                "zones": []
            }

    async def find_isolated_devices(self) -> List[str]:
        """
        Find devices with no connections.

        Returns:
            List of isolated device hostnames
        """
        query = """
        MATCH (d:Device)
        WHERE NOT (d)-[:CONNECTED_TO|ROUTES_TO]-()
        RETURN d.hostname as hostname
        ORDER BY hostname
        """

        try:
            result = await self.neo4j.execute_query(query, read_only=True)
            return [record["hostname"] for record in result]
        except Exception as e:
            logger.error(f"Failed to find isolated devices: {e}")
            return []

    def _process_path_data(self, path_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw path data from Neo4j.

        Args:
            path_data: Raw path data

        Returns:
            Processed path information
        """
        # This would process the path data structure
        # Implementation depends on exact Neo4j path format
        return {
            "path_data": path_data,
            "processed": True
        }