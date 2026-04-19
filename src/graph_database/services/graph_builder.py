"""
Graph builder service.
Converts ParsedDevice objects into Neo4j nodes and relationships.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from ...parser_engine.models.device import Device as ParsedDevice
from ...parser_engine.models.interface import Interface as ParsedInterface
from ...parser_engine.models.vlan import VLAN as ParsedVLAN
from ...parser_engine.models.routing import VRF as ParsedVRF
from ..config import GraphSettings
from ..models.graph_models import (
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
from .neo4j_service import Neo4jService

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Service for building graph structures from parsed network devices.

    Converts ParsedDevice objects into Neo4j nodes and relationships,
    handling batch operations and duplicate detection.
    """

    def __init__(self, neo4j_service: Neo4jService, settings: GraphSettings):
        """
        Initialize graph builder.

        Args:
            neo4j_service: Neo4j service instance
            settings: Graph database settings
        """
        self.neo4j = neo4j_service
        self.settings = settings
        self._node_cache: Dict[str, int] = {}  # Cache for node IDs by unique key

    async def build_device_graph(self, device: ParsedDevice, zone_name: Optional[str] = None) -> Dict[str, int]:
        """
        Build complete graph structure for a single device.

        Args:
            device: Parsed device from parser engine
            zone_name: Optional zone to place the device in

        Returns:
            Dictionary mapping object types to counts created/updated
        """
        stats = {
            "devices": 0,
            "interfaces": 0,
            "vlans": 0,
            "vrfs": 0,
            "zones": 0,
            "relationships": 0
        }

        try:
            # Create device node
            device_node = await self._create_or_update_device(device)
            stats["devices"] += 1

            # Create zone if specified
            zone_node_id = None
            if zone_name:
                zone_node = await self._create_or_update_zone(zone_name)
                zone_node_id = zone_node.node_id
                stats["zones"] += 1

                # Create LOCATED_IN relationship
                await self._create_located_in_relationship(device_node.node_id, zone_node_id)
                stats["relationships"] += 1

            # Create interfaces
            for interface in device.interfaces:
                interface_node = await self._create_or_update_interface(interface, device.hostname)
                stats["interfaces"] += 1

                # Create HAS_INTERFACE relationship
                await self._create_has_interface_relationship(device_node.node_id, interface_node.node_id)
                stats["relationships"] += 1

                # Create VLAN relationships
                vlan_rels = await self._create_vlan_relationships(interface, interface_node.node_id)
                stats["vlans"] += len(vlan_rels)
                stats["relationships"] += len(vlan_rels)

            # Create VLANs
            for vlan in device.vlans:
                vlan_node = await self._create_or_update_vlan(vlan)
                stats["vlans"] += 1

            # Create VRFs
            for vrf in device.vrfs:
                vrf_node = await self._create_or_update_vrf(vrf)
                stats["vrfs"] += 1

            # Create routing relationships
            route_rels = await self._create_routing_relationships(device)
            stats["relationships"] += route_rels

            logger.info(f"Built graph for device {device.hostname}: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to build graph for device {device.hostname}: {e}")
            raise

    async def build_devices_batch(self, devices: List[ParsedDevice], zone_name: Optional[str] = None) -> Dict[str, int]:
        """
        Build graph structures for multiple devices in batches.

        Args:
            devices: List of parsed devices
            zone_name: Optional zone for all devices

        Returns:
            Aggregated statistics
        """
        total_stats = {
            "devices": 0,
            "interfaces": 0,
            "vlans": 0,
            "vrfs": 0,
            "zones": 0,
            "relationships": 0
        }

        for i in range(0, len(devices), self.settings.graph_batch_size):
            batch = devices[i:i + self.settings.graph_batch_size]
            logger.info(f"Processing batch {i//self.settings.graph_batch_size + 1} with {len(batch)} devices")

            for device in batch:
                try:
                    stats = await self.build_device_graph(device, zone_name)
                    for key in total_stats:
                        total_stats[key] += stats[key]
                except Exception as e:
                    logger.error(f"Failed to process device {device.hostname}: {e}")
                    continue

        logger.info(f"Completed batch processing: {total_stats}")
        return total_stats

    async def _create_or_update_device(self, device: ParsedDevice) -> DeviceNode:
        """
        Create or update device node.

        Args:
            device: Parsed device

        Returns:
            DeviceNode instance
        """
        # Check if device already exists
        existing = await self.neo4j.find_node(
            labels=["Device"],
            properties={"hostname": device.hostname}
        )

        if existing:
            # Update existing node
            node_id = existing.get("id")
            update_query = """
            MATCH (d:Device {hostname: $hostname})
            SET d.vendor = $vendor,
                d.model = $model,
                d.os_version = $os_version,
                d.serial_number = $serial_number,
                d.updated_at = datetime()
            RETURN d
            """
            properties = {
                "hostname": device.hostname,
                "vendor": device.vendor.value if hasattr(device.vendor, 'value') else str(device.vendor),
                "model": device.model,
                "os_version": device.os_version,
                "serial_number": device.serial_number,
            }
            result = await self.neo4j.execute_query(update_query, properties)
            node_data = result[0]["d"] if result else existing
        else:
            # Create new node
            properties = {
                "hostname": device.hostname,
                "vendor": device.vendor.value if hasattr(device.vendor, 'value') else str(device.vendor),
                "model": device.model,
                "os_version": device.os_version,
                "serial_number": device.serial_number,
            }
            node_data = await self.neo4j.create_node(["Device"], properties)

        # Create DeviceNode instance
        device_node = DeviceNode(
            node_id=node_data.get("id"),
            hostname=device.hostname,
            vendor=device.vendor.value if hasattr(device.vendor, 'value') else str(device.vendor),
            model=device.model,
            os_version=device.os_version,
            serial_number=device.serial_number,
        )

        # Cache node ID
        self._node_cache[f"device:{device.hostname}"] = device_node.node_id

        return device_node

    async def _create_or_update_interface(self, interface: ParsedInterface, device_hostname: str) -> InterfaceNode:
        """
        Create or update interface node.

        Args:
            interface: Parsed interface
            device_hostname: Parent device hostname

        Returns:
            InterfaceNode instance
        """
        unique_key = f"interface:{device_hostname}:{interface.name}"

        # Check if interface already exists
        existing = await self.neo4j.find_node(
            labels=["Interface"],
            properties={"name": interface.name, "device_hostname": device_hostname}
        )

        if existing:
            # Update existing node
            update_query = """
            MATCH (i:Interface {name: $name, device_hostname: $device_hostname})
            SET i.interface_type = $interface_type,
                i.ip_address = $ip_address,
                i.state = $state,
                i.speed = $speed,
                i.duplex = $duplex,
                i.mtu = $mtu,
                i.description = $description,
                i.updated_at = datetime()
            RETURN i
            """
            properties = {
                "name": interface.name,
                "device_hostname": device_hostname,
                "interface_type": interface.interface_type.value if hasattr(interface.interface_type, 'value') else str(interface.interface_type),
                "ip_address": interface.ip_address,
                "state": interface.status.value if hasattr(interface.status, 'value') else str(interface.status),
                "speed": interface.speed,
                "duplex": interface.duplex,
                "mtu": interface.mtu,
                "description": interface.description,
            }
            result = await self.neo4j.execute_query(update_query, properties)
            node_data = result[0]["i"] if result else existing
        else:
            # Create new node
            properties = {
                "name": interface.name,
                "device_hostname": device_hostname,
                "interface_type": interface.interface_type.value if hasattr(interface.interface_type, 'value') else str(interface.interface_type),
                "ip_address": interface.ip_address,
                "state": interface.status.value if hasattr(interface.status, 'value') else str(interface.status),
                "speed": interface.speed,
                "duplex": interface.duplex,
                "mtu": interface.mtu,
                "description": interface.description,
            }
            node_data = await self.neo4j.create_node(["Interface"], properties)

        # Create InterfaceNode instance
        interface_node = InterfaceNode(
            node_id=node_data.get("id"),
            name=interface.name,
            interface_type=interface.interface_type.value if hasattr(interface.interface_type, 'value') else str(interface.interface_type),
            ip_address=interface.ip_address,
            state=interface.status.value if hasattr(interface.status, 'value') else str(interface.status),
            speed=interface.speed,
            duplex=interface.duplex,
            mtu=interface.mtu,
            description=interface.description,
        )

        # Cache node ID
        self._node_cache[unique_key] = interface_node.node_id

        return interface_node

    async def _create_or_update_vlan(self, vlan: ParsedVLAN) -> VLANNode:
        """
        Create or update VLAN node.

        Args:
            vlan: Parsed VLAN

        Returns:
            VLANNode instance
        """
        unique_key = f"vlan:{vlan.vlan_id}"

        # Return cached node if already created (e.g., by _create_vlan_relationships)
        if unique_key in self._node_cache:
            return VLANNode(
                node_id=self._node_cache[unique_key],
                vlan_id=vlan.vlan_id,
                name=vlan.name,
                description=getattr(vlan, "description", None),
            )

        # Check if VLAN already exists
        existing = await self.neo4j.find_node(
            labels=["VLAN"],
            properties={"vlan_id": vlan.vlan_id}
        )

        if existing:
            # Update existing node
            update_query = """
            MATCH (v:VLAN {vlan_id: $vlan_id})
            SET v.name = $name,
                v.description = $description,
                v.updated_at = datetime()
            RETURN v
            """
            properties = {
                "vlan_id": vlan.vlan_id,
                "name": vlan.name,
                "description": vlan.description,
            }
            result = await self.neo4j.execute_query(update_query, properties)
            node_data = result[0]["v"] if result else existing
        else:
            # Create new node
            properties = {
                "vlan_id": vlan.vlan_id,
                "name": vlan.name,
                "description": vlan.description,
            }
            node_data = await self.neo4j.create_node(["VLAN"], properties)

        # Create VLANNode instance
        vlan_node = VLANNode(
            node_id=node_data.get("id"),
            vlan_id=vlan.vlan_id,
            name=vlan.name,
            description=vlan.description,
        )

        # Cache node ID
        self._node_cache[unique_key] = vlan_node.node_id

        return vlan_node

    async def _create_or_update_vrf(self, vrf: ParsedVRF) -> VRFNode:
        """
        Create or update VRF node.

        Args:
            vrf: Parsed VRF

        Returns:
            VRFNode instance
        """
        unique_key = f"vrf:{vrf.name}"

        # Check if VRF already exists
        existing = await self.neo4j.find_node(
            labels=["VRF"],
            properties={"name": vrf.name}
        )

        if existing:
            # Update existing node
            update_query = """
            MATCH (v:VRF {name: $name})
            SET v.rd = $rd,
                v.rt_import = $rt_import,
                v.rt_export = $rt_export,
                v.updated_at = datetime()
            RETURN v
            """
            properties = {
                "name": vrf.name,
                "rd": vrf.rd,
                "rt_import": vrf.rt_import,
                "rt_export": vrf.rt_export,
            }
            result = await self.neo4j.execute_query(update_query, properties)
            node_data = result[0]["v"] if result else existing
        else:
            # Create new node
            properties = {
                "name": vrf.name,
                "rd": vrf.rd,
                "rt_import": vrf.rt_import,
                "rt_export": vrf.rt_export,
            }
            node_data = await self.neo4j.create_node(["VRF"], properties)

        # Create VRFNode instance
        vrf_node = VRFNode(
            node_id=node_data.get("id"),
            name=vrf.name,
            rd=vrf.rd,
            rt_import=vrf.rt_import,
            rt_export=vrf.rt_export,
        )

        # Cache node ID
        self._node_cache[unique_key] = vrf_node.node_id

        return vrf_node

    async def _create_or_update_zone(self, zone_name: str, zone_type: str = "network", security_level: int = 0) -> ZoneNode:
        """
        Create or update zone node.

        Args:
            zone_name: Zone name
            zone_type: Zone type
            security_level: Security level

        Returns:
            ZoneNode instance
        """
        unique_key = f"zone:{zone_name}"

        # Check if zone already exists
        existing = await self.neo4j.find_node(
            labels=["Zone"],
            properties={"name": zone_name}
        )

        if existing:
            node_data = existing
        else:
            # Create new node
            properties = {
                "name": zone_name,
                "zone_type": zone_type,
                "security_level": security_level,
            }
            node_data = await self.neo4j.create_node(["Zone"], properties)

        # Create ZoneNode instance
        zone_node = ZoneNode(
            node_id=node_data.get("id"),
            name=zone_name,
            zone_type=zone_type,
            security_level=security_level,
        )

        # Cache node ID
        self._node_cache[unique_key] = zone_node.node_id

        return zone_node

    async def _create_has_interface_relationship(self, device_id: int, interface_id: int) -> None:
        """
        Create HAS_INTERFACE relationship.

        Args:
            device_id: Device node ID
            interface_id: Interface node ID
        """
        await self.neo4j.create_relationship(
            device_id,
            interface_id,
            "HAS_INTERFACE"
        )

    async def _create_located_in_relationship(self, device_id: int, zone_id: int) -> None:
        """
        Create LOCATED_IN relationship.

        Args:
            device_id: Device node ID
            zone_id: Zone node ID
        """
        await self.neo4j.create_relationship(
            device_id,
            zone_id,
            "LOCATED_IN"
        )

    async def _create_vlan_relationships(self, interface: ParsedInterface, interface_id: int) -> List[int]:
        """
        Create VLAN relationships for an interface.

        Args:
            interface: Parsed interface
            interface_id: Interface node ID

        Returns:
            List of created relationship counts
        """
        relationships_created = []

        # Access VLAN
        if interface.access_vlan:
            vlan_node = await self._create_or_update_vlan_from_id(interface.access_vlan)
            await self.neo4j.create_relationship(
                interface_id,
                vlan_node.node_id,
                "MEMBER_OF_VLAN",
                {"mode": "access"}
            )
            relationships_created.append(1)

        # Trunk VLANs
        if interface.trunk_vlans:
            for vlan_id in interface.trunk_vlans:
                vlan_node = await self._create_or_update_vlan_from_id(vlan_id)
                is_native = vlan_id == interface.native_vlan
                await self.neo4j.create_relationship(
                    interface_id,
                    vlan_node.node_id,
                    "MEMBER_OF_VLAN",
                    {"mode": "trunk", "native": is_native}
                )
                relationships_created.append(1)

        return relationships_created

    async def _create_or_update_vlan_from_id(self, vlan_id: int) -> VLANNode:
        """
        Create or get VLAN node by ID only.

        Args:
            vlan_id: VLAN ID

        Returns:
            VLANNode instance
        """
        unique_key = f"vlan:{vlan_id}"

        if unique_key in self._node_cache:
            # Get existing node data
            existing = await self.neo4j.find_node(
                labels=["VLAN"],
                properties={"vlan_id": vlan_id}
            )
            if existing:
                return VLANNode(
                    node_id=existing.get("id"),
                    vlan_id=vlan_id,
                    name=existing.get("name"),
                )

        # Create new VLAN node
        properties = {"vlan_id": vlan_id}
        node_data = await self.neo4j.create_node(["VLAN"], properties)

        vlan_node = VLANNode(
            node_id=node_data.get("id"),
            vlan_id=vlan_id,
        )

        self._node_cache[unique_key] = vlan_node.node_id
        return vlan_node

    async def _create_routing_relationships(self, device: ParsedDevice) -> int:
        """
        Create routing relationships for a device.

        Args:
            device: Parsed device

        Returns:
            Number of relationships created
        """
        relationships_created = 0

        # Static routes
        for route in device.static_routes:
            if route.next_hop:
                # Find or create target device (simplified - in real implementation
                # would need IP to hostname resolution)
                target_hostname = f"device_via_{route.next_hop}"
                await self.neo4j.create_relationship(
                    self._node_cache[f"device:{device.hostname}"],
                    0,  # Would need to resolve target device ID
                    "ROUTES_TO",
                    {
                        "protocol": "static",
                        "network": f"{route.network}/{route.prefix_length}",
                        "next_hop": route.next_hop,
                        "metric": route.metric,
                    }
                )
                relationships_created += 1

        return relationships_created

    def clear_cache(self) -> None:
        """
        Clear the node cache.
        """
        self._node_cache.clear()
        logger.info("Node cache cleared")