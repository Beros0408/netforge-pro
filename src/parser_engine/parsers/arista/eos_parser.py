"""
Arista EOS configuration parser.

Supports:
  - Hostname detection
  - EOS version string
  - Interfaces (L2 and L3, with IP, description, shutdown, VLANs)
  - VLANs (database and interface-level)
  - Static routes (ip route)
  - OSPF (router ospf)
  - BGP (router bgp)
  - ACLs (ip access-list)
"""
from __future__ import annotations

import re
from typing import Optional

from ...models.device import Device, VendorType
from ...models.interface import Interface, InterfaceStatus, SwitchportMode, detect_interface_type
from ...models.vlan import VLAN, VLANStatus, parse_vlan_range
from ...models.routing import (
    Route,
    RouteProtocol,
    OSPFProcess,
    OSPFNetwork,
    OSPFRedistribution,
    BGPProcess,
    BGPNeighbor,
    BGPNetwork,
    VRF,
)
from ...models.security import ACL, ACLEntry, ACLAction, ACLType
from ..base_parser import BaseParser, ParserError

# ---------------------------------------------------------------------------
# Compiled regular expressions
# ---------------------------------------------------------------------------

_RE_HOSTNAME = re.compile(r"^hostname\s+(\S+)", re.MULTILINE)
_RE_VERSION = re.compile(r"(?:Arista\s+)?EOS\s+version\s+([\d.]+[A-Z]?)", re.MULTILINE)
_RE_MODEL = re.compile(r"!\s*Model:\s*(.+)", re.MULTILINE)
_RE_SERIAL = re.compile(r"!\s*Serial Number:\s*(.+)", re.MULTILINE)
_RE_INTERFACE_HEADER = re.compile(r"^interface\s+(\S+)", re.MULTILINE)
_RE_IP_ADDRESS = re.compile(
    r"^\s+ip address\s+(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?",
    re.MULTILINE,
)
_RE_DESCRIPTION = re.compile(r"^\s+description\s+(.*)", re.MULTILINE)
_RE_SHUTDOWN = re.compile(r"^\s+shutdown\s*$", re.MULTILINE)
_RE_VRF_FORWARDING = re.compile(r"^\s+vrf forwarding\s+(\S+)", re.MULTILINE)
_RE_SWITCHPORT_MODE = re.compile(r"^\s+switchport mode\s+(\S+)", re.MULTILINE)
_RE_SWITCHPORT_ACCESS_VLAN = re.compile(
    r"^\s+switchport access vlan\s+(\d+)", re.MULTILINE
)
_RE_SWITCHPORT_TRUNK_ALLOWED = re.compile(
    r"^\s+switchport trunk allowed vlan\s+(\S+)", re.MULTILINE
)
_RE_SWITCHPORT_TRUNK_NATIVE = re.compile(
    r"^\s+switchport trunk native vlan\s+(\d+)", re.MULTILINE
)
_RE_MTU = re.compile(r"^\s+mtu\s+(\d+)", re.MULTILINE)
_RE_SPEED = re.compile(r"^\s+speed\s+(\S+)", re.MULTILINE)
_RE_DUPLEX = re.compile(r"^\s+duplex\s+(\S+)", re.MULTILINE)
_RE_VXLAN_VLAN_VNI = re.compile(r"^\s+vxlan vlan\s+(\d+)\s+vni\s+(\d+)", re.MULTILINE)
_RE_VLAN_HEADER = re.compile(r"^vlan\s+(\d+)", re.MULTILINE)
_RE_VLAN_NAME = re.compile(r"^\s+name\s+(\S+)", re.MULTILINE)
_RE_VLAN_STATE = re.compile(r"^\s+state\s+(\S+)", re.MULTILINE)
_RE_IP_ROUTE = re.compile(
    r"^ip route\s+(?:vrf\s+(\S+)\s+)?(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?\s+(\S+)(?:\s+(\d+))?",
    re.MULTILINE,
)
_RE_OSPF_HEADER = re.compile(r"^router ospf\s+(\d+)(?:\s+vrf\s+(\S+))?", re.MULTILINE)
_RE_OSPF_ROUTER_ID = re.compile(r"^\s+router-id\s+(\S+)", re.MULTILINE)
_RE_OSPF_NETWORK = re.compile(
    r"^\s+network\s+(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?\s+area\s+(\S+)",
    re.MULTILINE,
)
_RE_OSPF_REDISTRIBUTE = re.compile(
    r"^\s+redistribute\s+(\S+)(?:\s+metric\s+(\d+))?(?:\s+metric-type\s+(\S+))?",
    re.MULTILINE,
)
_RE_BGP_HEADER = re.compile(r"^router bgp\s+(\d+)", re.MULTILINE)
_RE_BGP_ROUTER_ID = re.compile(r"^\s+(?:bgp\s+)?router-id\s+(\S+)", re.MULTILINE)
_RE_BGP_NEIGHBOR = re.compile(r"^\s+neighbor\s+(\S+)\s+remote-as\s+(\d+)", re.MULTILINE)
_RE_BGP_NEIGHBOR_DESC = re.compile(r"^\s+neighbor\s+(\S+)\s+description\s+(.*)", re.MULTILINE)
_RE_BGP_NEIGHBOR_PEER_GROUP = re.compile(r"^\s+neighbor\s+(\S+)\s+peer group\s+(\S+)", re.MULTILINE)
_RE_BGP_NETWORK = re.compile(r"^\s+network\s+(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?", re.MULTILINE)
_RE_VRF_HEADER = re.compile(r"^vrf instance\s+(\S+)", re.MULTILINE)
_RE_VRF_RD = re.compile(r"^\s+rd\s+(\S+)", re.MULTILINE)
_RE_ACL_HEADER = re.compile(r"^ip access-list\s+(?:extended\s+)?(\S+)", re.MULTILINE)
_RE_ACL_ENTRY = re.compile(
    r"^\s+(\d+)\s+(permit|deny)\s+(.+)", re.MULTILINE
)


class AristaEOSParser(BaseParser):
    """
    Parser for Arista EOS running configurations.

    Identifies device attributes, interfaces, VLANs, routing protocols,
    and ACLs from Arista EOS configurations.

    Example::

        parser = AristaEOSParser()
        if parser.can_parse(config_text):
            result = await parser.parse(config_text)
            print(result.device.hostname)
    """

    vendor: VendorType = VendorType.ARISTA_EOS
    parser_version: str = "1.0.0"

    # Keywords that appear in Arista EOS configs
    _ARISTA_FINGERPRINTS = (
        "arista",
        "ARISTA",
        "eos version",
        "EOS-",
        "ceoslab",
        "veos",
        "running-config",
        "startup-config",
    )

    # ------------------------------------------------------------------
    # BaseParser interface
    # ------------------------------------------------------------------

    def can_parse(self, raw_config: str) -> bool:
        """
        Return True when the config looks like an Arista EOS configuration.

        Checks the first 30 lines for well-known Arista strings.

        Args:
            raw_config: Full configuration text.

        Returns:
            True for Arista EOS configurations.
        """
        header = "\n".join(raw_config.splitlines()[:30]).lower()
        return any(fp.lower() in header for fp in self._ARISTA_FINGERPRINTS)

    async def _do_parse(self, raw_config: str) -> Device:
        """
        Parse an Arista EOS configuration and return a Device.

        Args:
            raw_config: Full configuration text.

        Returns:
            Fully populated Device model.
        """
        lines = raw_config.splitlines()
        device = Device(
            hostname=self._extract_hostname(lines),
            vendor=self.vendor,
            os_version=self._extract_version(raw_config),
            model=self._extract_model(raw_config),
            serial_number=self._extract_serial(raw_config),
            interfaces=[],
            vlans=[],
            static_routes=[],
            ospf_processes=[],
            bgp_processes=[],
            vrfs=[],
            vxlan_vni_mappings={},
            acls=[],
            firewall_policies=[],
            nat_rules=[],
            raw_config=raw_config,
        )

        # Parse interfaces
        device.interfaces = self._parse_interfaces(lines)

        # Parse VXLAN
        device.vxlan_vni_mappings = self._parse_vxlan(lines)

        # Parse VLANs
        device.vlans = self._parse_vlans(lines)

        # Parse VRFs
        device.vrfs = self._parse_vrfs(lines)

        # Parse routing
        device.static_routes = self._parse_static_routes(lines)
        device.ospf_processes = self._parse_ospf(lines)
        device.bgp_processes = self._parse_bgp(lines)

        # Parse security
        device.acls = self._parse_acls(lines)

        return device

    # ------------------------------------------------------------------
    # Private parsing methods
    # ------------------------------------------------------------------

    def _extract_hostname(self, lines: list[str]) -> str:
        """Extract hostname from hostname command."""
        for line in lines:
            if match := _RE_HOSTNAME.match(line):
                return match.group(1)
        return "unknown"

    def _extract_version(self, raw_config: str) -> str:
        """Extract EOS version from configuration."""
        if match := _RE_VERSION.search(raw_config):
            return match.group(1)
        return "unknown"

    def _extract_model(self, raw_config: str) -> Optional[str]:
        """Extract model from configuration comments."""
        if match := _RE_MODEL.search(raw_config):
            return match.group(1).strip()
        return None

    def _extract_serial(self, raw_config: str) -> Optional[str]:
        """Extract serial number from configuration comments."""
        if match := _RE_SERIAL.search(raw_config):
            return match.group(1).strip()
        return None

    def _parse_interfaces(self, lines: list[str]) -> list[Interface]:
        """Parse interface configurations."""
        interfaces = []
        current_iface = None
        iface_config = []

        for line in lines:
            # New interface section
            if match := _RE_INTERFACE_HEADER.match(line):
                # Save previous interface if exists
                if current_iface:
                    interfaces.append(self._build_interface(current_iface, iface_config))

                current_iface = match.group(1)
                iface_config = []
            elif current_iface and line.startswith(" "):
                # Continuation of current interface
                iface_config.append(line)
            elif current_iface and not line.startswith(" "):
                # End of interface section
                interfaces.append(self._build_interface(current_iface, iface_config))
                current_iface = None
                iface_config = []

        # Handle last interface
        if current_iface:
            interfaces.append(self._build_interface(current_iface, iface_config))

        return interfaces

    def _parse_vxlan(self, lines: list[str]) -> dict[int, int]:
        """Parse VXLAN VNI mappings from Vxlan1 interface."""
        vxlan_mappings = {}
        in_vxlan_interface = False

        for line in lines:
            if match := _RE_INTERFACE_HEADER.match(line):
                interface_name = match.group(1)
                in_vxlan_interface = interface_name.lower() == "vxlan1"
            elif in_vxlan_interface and line.startswith(" "):
                if match := _RE_VXLAN_VLAN_VNI.match(line):
                    vlan_id = int(match.group(1))
                    vni = int(match.group(2))
                    vxlan_mappings[vlan_id] = vni
            elif in_vxlan_interface and not line.startswith(" "):
                # End of Vxlan1 interface
                break

        return vxlan_mappings

    def _build_interface(self, name: str, config_lines: list[str]) -> Interface:
        """Build Interface object from configuration lines."""
        iface = Interface(
            name=name,
            description=None,
            interface_type=detect_interface_type(name),
            admin_status=True,
            status=InterfaceStatus.UP,
            ip_address=None,
            subnet_mask=None,
            prefix_length=None,
            secondary_ips=[],
            mtu=1500,
            speed=None,
            duplex=None,
            switchport_mode=SwitchportMode.ACCESS,
            access_vlan=None,
            trunk_vlans=[],
            native_vlan=None,
            vrf=None,
            channel_group=None,
        )

        for line in config_lines:
            if match := _RE_DESCRIPTION.match(line):
                iface.description = match.group(1)
            elif _RE_SHUTDOWN.match(line):
                iface.admin_status = False
                iface.status = InterfaceStatus.ADMIN_DOWN
            elif match := _RE_IP_ADDRESS.match(line):
                ip, prefix = match.groups()
                iface.ip_address = ip
                if prefix:
                    iface.prefix_length = int(prefix)
                else:
                    # EOS uses CIDR natively, assume /24 if not specified
                    iface.prefix_length = 24
            elif match := _RE_VRF_FORWARDING.match(line):
                iface.vrf = match.group(1)
            elif match := _RE_SWITCHPORT_MODE.match(line):
                mode = match.group(1)
                if mode == "trunk":
                    iface.switchport_mode = SwitchportMode.TRUNK
                elif mode == "access":
                    iface.switchport_mode = SwitchportMode.ACCESS
            elif match := _RE_SWITCHPORT_ACCESS_VLAN.match(line):
                iface.access_vlan = int(match.group(1))
            elif match := _RE_SWITCHPORT_TRUNK_ALLOWED.match(line):
                vlan_spec = match.group(1)
                iface.trunk_vlans = parse_vlan_range(vlan_spec)
            elif match := _RE_SWITCHPORT_TRUNK_NATIVE.match(line):
                iface.native_vlan = int(match.group(1))
            elif match := _RE_MTU.match(line):
                iface.mtu = int(match.group(1))
            elif match := _RE_SPEED.match(line):
                speed_value = match.group(1)
                if speed_value.isdigit():
                    iface.speed = int(speed_value)
                elif speed_value.lower().endswith("g"):
                    iface.speed = int(speed_value[:-1]) * 1000
            elif match := _RE_DUPLEX.match(line):
                iface.duplex = match.group(1)

        return iface

    def _normalize_interface_name(self, name: str) -> str:
        """Normalize Arista interface names to standard format."""
        # Convert to standard abbreviations
        name = re.sub(r"Ethernet", "Et", name)
        name = re.sub(r"Vlan", "Vl", name)
        name = re.sub(r"Port-Channel", "Po", name)
        name = re.sub(r"Loopback", "Lo", name)
        name = re.sub(r"Management", "Ma", name)
        name = re.sub(r"Vxlan", "Vx", name)
        return name.lower()

    def _parse_vlans(self, lines: list[str]) -> list[VLAN]:
        """Parse VLAN configurations."""
        vlans = []
        current_vlan = None
        vlan_config = []

        for line in lines:
            if match := _RE_VLAN_HEADER.match(line):
                if current_vlan:
                    vlans.append(self._build_vlan(current_vlan, vlan_config))

                current_vlan = int(match.group(1))
                vlan_config = []
            elif current_vlan and line.startswith(" "):
                vlan_config.append(line)
            elif current_vlan and not line.startswith(" "):
                vlans.append(self._build_vlan(current_vlan, vlan_config))
                current_vlan = None
                vlan_config = []

        if current_vlan:
            vlans.append(self._build_vlan(current_vlan, vlan_config))

        return vlans

    def _build_vlan(self, vlan_id: int, config_lines: list[str]) -> VLAN:
        """Build VLAN object from configuration."""
        vlan = VLAN(
            vlan_id=vlan_id,
            name=f"VLAN{vlan_id}",
            status=VLANStatus.ACTIVE,
            interfaces=[],
        )

        for line in config_lines:
            if match := _RE_VLAN_NAME.match(line):
                vlan.name = match.group(1)
            elif match := _RE_VLAN_STATE.match(line):
                state = match.group(1).lower()
                if state == "suspend":
                    vlan.status = VLANStatus.SUSPEND
                else:
                    vlan.status = VLANStatus.ACTIVE

        return vlan

    def _parse_static_routes(self, lines: list[str]) -> list[Route]:
        """Parse static routes."""
        routes = []
        for line in lines:
            if match := _RE_IP_ROUTE.match(line):
                vrf, network, prefix, next_hop, distance = match.groups()
                if prefix:
                    network_with_prefix = f"{network}/{prefix}"
                else:
                    # EOS uses CIDR natively, assume /24 if not specified
                    network_with_prefix = f"{network}/24"
                
                routes.append(Route(
                    network=network_with_prefix,
                    next_hop=next_hop,
                    protocol=RouteProtocol.STATIC,
                    admin_distance=int(distance) if distance else 1,
                    metric=0,
                    vrf=vrf,
                ))
        return routes

    def _parse_ospf(self, lines: list[str]) -> list[OSPFProcess]:
        """Parse OSPF configurations."""
        processes = []
        current_process = None
        process_config = []

        for line in lines:
            if match := _RE_OSPF_HEADER.match(line):
                if current_process:
                    processes.append(self._build_ospf_process(current_process, process_config))

                current_process = int(match.group(1))
                process_config = []
            elif current_process and line.startswith(" "):
                process_config.append(line)
            elif current_process and not line.startswith(" "):
                processes.append(self._build_ospf_process(current_process, process_config))
                current_process = None
                process_config = []

        if current_process:
            processes.append(self._build_ospf_process(current_process, process_config))

        return processes

    def _build_ospf_process(self, process_id: int, config_lines: list[str]) -> OSPFProcess:
        """Build OSPF process from configuration."""
        process = OSPFProcess(
            process_id=process_id,
            router_id=None,
            networks=[],
            passive_interfaces=[],
            redistributions=[],
        )

        for line in config_lines:
            if match := _RE_OSPF_ROUTER_ID.match(line):
                process.router_id = match.group(1)
            elif match := _RE_OSPF_NETWORK.match(line):
                network, prefix, area = match.groups()
                if prefix:
                    process.networks.append(OSPFNetwork(
                        network=f"{network}/{prefix}",
                        area=area,
                    ))
                else:
                    # Assume /24 if no prefix
                    process.networks.append(OSPFNetwork(
                        network=f"{network}/24",
                        area=area,
                    ))
            elif match := _RE_OSPF_REDISTRIBUTE.match(line):
                protocol, metric, metric_type = match.groups()
                redistribution = OSPFRedistribution(
                    source_protocol=protocol,
                    metric=int(metric) if metric else None,
                    metric_type=int(metric_type) if metric_type else None,
                )
                process.redistributions.append(redistribution)

        return process

    def _parse_bgp(self, lines: list[str]) -> list[BGPProcess]:
        """Parse BGP configurations."""
        processes = []
        current_process = None
        process_config = []

        for line in lines:
            if match := _RE_BGP_HEADER.match(line):
                if current_process:
                    processes.append(self._build_bgp_process(current_process, process_config))

                current_process = int(match.group(1))
                process_config = []
            elif current_process and line.startswith(" "):
                process_config.append(line)
            elif current_process and not line.startswith(" "):
                processes.append(self._build_bgp_process(current_process, process_config))
                current_process = None
                process_config = []

        if current_process:
            processes.append(self._build_bgp_process(current_process, process_config))

        return processes

    def _build_bgp_process(self, asn: int, config_lines: list[str]) -> BGPProcess:
        """Build BGP process from configuration."""
        process = BGPProcess(
            local_as=asn,
            router_id=None,
            neighbors=[],
            networks=[],
        )

        for line in config_lines:
            if match := _RE_BGP_ROUTER_ID.match(line):
                process.router_id = match.group(1)
            elif match := _RE_BGP_NEIGHBOR.match(line):
                address, remote_as = match.groups()
                neighbor = BGPNeighbor(
                    address=address,
                    remote_as=int(remote_as),
                    description=None,
                    peer_group=None,
                )
                # Check for description and peer group
                for desc_line in config_lines:
                    if desc_match := _RE_BGP_NEIGHBOR_DESC.match(desc_line):
                        if desc_match.group(1) == address:
                            neighbor.description = desc_match.group(2)
                            break
                    elif pg_match := _RE_BGP_NEIGHBOR_PEER_GROUP.match(desc_line):
                        if pg_match.group(1) == address:
                            neighbor.peer_group = pg_match.group(2)
                            break
                process.neighbors.append(neighbor)
            elif match := _RE_BGP_NETWORK.match(line):
                network, prefix = match.groups()
                if prefix:
                    network_str = f"{network}/{prefix}"
                else:
                    # Assume /24 if no prefix
                    network_str = f"{network}/24"
                process.networks.append(BGPNetwork(network=network_str))

        return process

    def _parse_vrfs(self, lines: list[str]) -> list[VRF]:
        """Parse VRF configurations."""
        vrfs = []
        current_vrf = None
        vrf_config = []

        for line in lines:
            if match := _RE_VRF_HEADER.match(line):
                if current_vrf:
                    vrfs.append(self._build_vrf(current_vrf, vrf_config))

                current_vrf = match.group(1)
                vrf_config = []
            elif current_vrf and line.startswith(" "):
                vrf_config.append(line)
            elif current_vrf and not line.startswith(" "):
                vrfs.append(self._build_vrf(current_vrf, vrf_config))
                current_vrf = None
                vrf_config = []

        if current_vrf:
            vrfs.append(self._build_vrf(current_vrf, vrf_config))

        return vrfs

    def _build_vrf(self, name: str, config_lines: list[str]) -> VRF:
        """Build VRF object from configuration."""
        vrf = VRF(
            name=name,
            rd=None,
            interfaces=[],
        )

        for line in config_lines:
            if match := _RE_VRF_RD.match(line):
                vrf.rd = match.group(1)

        return vrf

    def _parse_acls(self, lines: list[str]) -> list[ACL]:
        """Parse ACL configurations."""
        acls = []
        current_acl = None
        acl_config = []

        for line in lines:
            if match := _RE_ACL_HEADER.match(line):
                if current_acl:
                    acls.append(self._build_acl(current_acl, acl_config))

                current_acl = match.group(1)
                acl_config = []
            elif current_acl and line.startswith(" "):
                acl_config.append(line)
            elif current_acl and not line.startswith(" "):
                acls.append(self._build_acl(current_acl, acl_config))
                current_acl = None
                acl_config = []

        if current_acl:
            acls.append(self._build_acl(current_acl, acl_config))

        return acls

    def _build_acl(self, acl_name: str, config_lines: list[str]) -> ACL:
        """Build ACL from configuration."""
        acl = ACL(
            name=acl_name,
            acl_type=ACLType.IPV4_EXTENDED,  # Arista ACLs are typically extended
            entries=[],
        )

        for line in config_lines:
            if match := _RE_ACL_ENTRY.match(line):
                sequence, action, rule_spec = match.groups()
                tokens = rule_spec.split()
                protocol = tokens[0] if tokens else None
                source = tokens[1] if len(tokens) > 1 else None
                destination = " ".join(tokens[2:]) if len(tokens) > 2 else None

                acl.entries.append(ACLEntry(
                    sequence=int(sequence),
                    action=ACLAction.PERMIT if action == "permit" else ACLAction.DENY,
                    protocol=protocol,
                    source=source,
                    destination=destination,
                ))

        return acl