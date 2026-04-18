"""
Huawei VRP parser for NetForge Pro.

Supports Huawei CE/AR/S series running VRP. Parses device metadata,
interfaces, VLANs, static routes, OSPF, BGP, VRFs, ACLs and outbound NAT.
"""

from __future__ import annotations

import re
from typing import Optional

from ...models.device import Device, OSType, VendorType
from ...models.interface import (
    Interface,
    InterfaceStatus,
    InterfaceType,
    SwitchportMode,
    detect_interface_type,
)
from ...models.vlan import VLAN, parse_vlan_range
from ...models.routing import (
    Route,
    RouteProtocol,
    OSPFProcess,
    OSPFNetwork,
    BGPProcess,
    BGPNeighbor,
    VRF,
)
from ...models.security import ACL, ACLEntry, ACLAction, ACLType, NATRule, NATType
from ..base_parser import BaseParser


# ---------------------------------------------------------------------------
# Compiled regular expressions
# ---------------------------------------------------------------------------

_VENDOR_PATTERNS = [
    r"Huawei",
    r"HUAWEI",
    r"VRP\s+\(R\)\s+software",
    r"Versatile\s+Routing\s+Platform",
    r"\bCE\d+\b",
    r"\bAR\d+\b",
    r"\bS\d{4}\b",
    r"^sysname\s+",
    r"^interface\s+(?:GigabitEthernet\d+/\d+/\d+|Vlanif|Eth-Trunk|LoopBack)",
]

_RE_OS_VERSION = re.compile(r"VRP\s+\(R\)\s+software,\s+Version\s+([\d.]+)", re.IGNORECASE)
_RE_MODEL = re.compile(r"^Huawei\s+(\S+)\s+Routing\s+Switch", re.IGNORECASE | re.MULTILINE)
_RE_HOSTNAME = re.compile(r"^sysname\s+(\S+)", re.MULTILINE)
_RE_INTERFACE_BLOCK = re.compile(r"^interface\s+(.+?)\n(.*?)(?=^interface\s|\Z)", re.MULTILINE | re.DOTALL)
_RE_DESCRIPTION = re.compile(r"^\s+description\s+(.+)$", re.MULTILINE)
_RE_SHUTDOWN = re.compile(r"^\s+shutdown\s*$", re.MULTILINE)
_RE_IP_ADDRESS = re.compile(
    r"^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)",
    re.MULTILINE,
)
_RE_SECONDARY_IP = re.compile(
    r"^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+sub",
    re.MULTILINE,
)
_RE_VRF_BINDING = re.compile(r"^\s+ip\s+binding\s+vpn-instance\s+(\S+)", re.MULTILINE)
_RE_SPEED = re.compile(r"^\s+speed\s+(\d+)", re.MULTILINE)
_RE_DUPLEX = re.compile(r"^\s+duplex\s+(\S+)", re.MULTILINE)
_RE_MTU = re.compile(r"^\s+mtu\s+(\d+)", re.MULTILINE)
_RE_PORT_ACCESS = re.compile(r"^\s+port\s+link-type\s+access", re.MULTILINE)
_RE_PORT_TRUNK = re.compile(r"^\s+port\s+link-type\s+trunk", re.MULTILINE)
_RE_PORT_HYBRID = re.compile(r"^\s+port\s+link-type\s+hybrid", re.MULTILINE)
_RE_ACCESS_VLAN = re.compile(r"^\s+port\s+default\s+vlan\s+(\d+)", re.MULTILINE)
_RE_TRUNK_VLANS = re.compile(
    r"^\s+port\s+trunk\s+allow-pass\s+vlan\s+([\d\s]+(?:to\s+\d+)?)",
    re.MULTILINE,
)
_RE_VLAN_BATCH = re.compile(r"^vlan\s+batch\s+(.+)$", re.MULTILINE)
_RE_VLAN_BLOCK = re.compile(r"^vlan\s+(\d+)[^\S\n]*(.*?)((?=^vlan\s)|\Z)", re.MULTILINE | re.DOTALL)
_RE_OSPF_AREA_BLOCK = re.compile(r"^\s+area\s+(\S+)(.*?)(?=^\s+area\s|\Z)", re.MULTILINE | re.DOTALL)
_RE_OSPF_AREA_NETWORK = re.compile(r"^\s+network\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)", re.MULTILINE)
_RE_ACL_DESC = re.compile(r"^\s+description\s+(.+)$", re.MULTILINE)
_RE_VLAN_NAME = re.compile(r"^\s+name\s+(.+)$", re.MULTILINE)
_RE_VLAN_DESC = re.compile(r"^\s+description\s+(.+)$", re.MULTILINE)
_RE_STATIC_ROUTE = re.compile(
    r"^ip\s+route-static\s+"
    r"(?:vpn-instance\s+(\S+)\s+)?"
    r"(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+"
    r"(\S+)"
    r"(?:\s+preference\s+(\d+))?",
    re.MULTILINE,
)
_RE_OSPF_PROCESS = re.compile(r"^ospf\s+(\d+)(.*?)(?=^ospf\s|\Z)", re.MULTILINE | re.DOTALL)
_RE_OSPF_ROUTER_ID = re.compile(r"^\s+router-id\s+(\d+\.\d+\.\d+\.\d+)", re.MULTILINE)
_RE_OSPF_NETWORK = re.compile(
    r"^\s+network\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+area\s+(\S+)",
    re.MULTILINE,
)
_RE_BGP_PROCESS = re.compile(r"^bgp\s+(\d+)(.*?)(?=^bgp\s|\Z)", re.MULTILINE | re.DOTALL)
_RE_BGP_ROUTER_ID = re.compile(r"^\s+router-id\s+(\d+\.\d+\.\d+\.\d+)", re.MULTILINE)
_RE_BGP_PEER = re.compile(
    r"^\s+peer\s+(\d+\.\d+\.\d+\.\d+)\s+as-number\s+(\d+)",
    re.MULTILINE,
)
_RE_BGP_PEER_DESC = re.compile(
    r"^\s+peer\s+(\d+\.\d+\.\d+\.\d+)\s+description\s+(.+)$",
    re.MULTILINE,
)
_RE_VRF_BLOCK = re.compile(r"^ip\s+vpn-instance\s+(\S+)(.*?)(?=^ip\s+vpn-instance\s|\Z)", re.MULTILINE | re.DOTALL)
_RE_VRF_RD = re.compile(r"^\s+route-distinguisher\s+(.+)$", re.MULTILINE)
_RE_VRF_RT_IMPORT = re.compile(r"^\s+vpn-target\s+(.+?)\s+import-extcommunity", re.MULTILINE)
_RE_VRF_RT_EXPORT = re.compile(r"^\s+vpn-target\s+(.+?)\s+export-extcommunity", re.MULTILINE)
_RE_ACL_BASIC = re.compile(r"^acl\s+(?:number\s+)?(\d+)(.*?)(?=^acl\s|\Z)", re.MULTILINE | re.DOTALL)
_RE_ACL_NAMED = re.compile(r"^acl\s+name\s+(\S+)(?:\s+advance)?(.*?)(?=^acl\s|\Z)", re.MULTILINE | re.DOTALL)
_RE_ACL_RULE = re.compile(
    r"^\s+rule\s+(\d+)\s+(permit|deny)\s+(\S+)\s+(.+)$",
    re.MULTILINE,
)
_RE_NAT_OUTBOUND = re.compile(
    r"^\s+nat\s+outbound\s+(\d+)(?:\s+address-group\s+(\d+))?",
    re.MULTILINE,
)


class HuaweiVRPParser(BaseParser):
    """Huawei VRP parser implementation."""

    vendor: VendorType = VendorType.HUAWEI_VRP
    parser_version: str = "1.0.0"

    def can_parse(self, raw_config: str) -> bool:
        header = "\n".join(raw_config.splitlines()[:40])
        return any(
            re.search(pattern, header, re.IGNORECASE | re.MULTILINE)
            for pattern in _VENDOR_PATTERNS
        )

    async def _do_parse(self, raw_config: str) -> Device:
        lines = raw_config.splitlines()
        device = Device(
            hostname=self._parse_hostname(raw_config),
            vendor=self.vendor,
            os_type=OSType.VRP,
            os_version=self._parse_version(raw_config),
            model=self._parse_model(raw_config),
            serial_number=None,
            interfaces=self._parse_interfaces(raw_config),
            vlans=self._parse_vlans(raw_config),
            static_routes=self._parse_static_routes(raw_config),
            ospf_processes=self._parse_ospf(raw_config),
            bgp_processes=self._parse_bgp(raw_config),
            vrfs=self._parse_vrfs(raw_config),
            acls=self._parse_acls(raw_config),
            firewall_policies=[],
            nat_rules=self._parse_nat(raw_config),
            raw_config=raw_config,
        )
        return device

    def _parse_hostname(self, raw_config: str) -> str:
        match = _RE_HOSTNAME.search(raw_config)
        return match.group(1) if match else "unknown"

    def _parse_version(self, raw_config: str) -> str:
        match = _RE_OS_VERSION.search(raw_config)
        return match.group(1) if match else "unknown"

    def _parse_model(self, raw_config: str) -> Optional[str]:
        match = _RE_MODEL.search(raw_config)
        return match.group(1) if match else None

    def _parse_interfaces(self, raw_config: str) -> list[Interface]:
        result: list[Interface] = []
        for match in _RE_INTERFACE_BLOCK.finditer(raw_config):
            raw_name = match.group(1).strip()
            block = match.group(2)
            result.append(self._parse_interface(raw_name, block))
        return result

    def _parse_interface(self, raw_name: str, block: str) -> Interface:
        description = None
        if m := _RE_DESCRIPTION.search(block):
            description = m.group(1).strip()

        enabled = not bool(_RE_SHUTDOWN.search(block))
        speed = int(_RE_SPEED.search(block).group(1)) if _RE_SPEED.search(block) else None
        duplex = _RE_DUPLEX.search(block).group(1) if _RE_DUPLEX.search(block) else None
        mtu = int(_RE_MTU.search(block).group(1)) if _RE_MTU.search(block) else None

        ip_address = None
        subnet_mask = None
        prefix_length = None
        if m := _RE_IP_ADDRESS.search(block):
            ip_address, subnet_mask = m.groups()
            prefix_length = self._mask_to_prefix_length(subnet_mask)

        secondary_ips: list[str] = []
        for m in _RE_SECONDARY_IP.finditer(block):
            ip, mask = m.groups()
            secondary_ips.append(f"{ip}/{self._mask_to_prefix_length(mask)}")

        vrf = _RE_VRF_BINDING.search(block)
        vrf_name = vrf.group(1) if vrf else None

        switchport_mode = SwitchportMode.ROUTED
        access_vlan = None
        trunk_vlans: list[int] = []
        if _RE_PORT_ACCESS.search(block):
            switchport_mode = SwitchportMode.ACCESS
            if m := _RE_ACCESS_VLAN.search(block):
                access_vlan = int(m.group(1))
        elif _RE_PORT_TRUNK.search(block):
            switchport_mode = SwitchportMode.TRUNK
            if m := _RE_TRUNK_VLANS.search(block):
                trunk_vlans = parse_vlan_range(m.group(1))
        elif _RE_PORT_HYBRID.search(block):
            switchport_mode = SwitchportMode.HYBRID
            if m := _RE_TRUNK_VLANS.search(block):
                trunk_vlans = parse_vlan_range(m.group(1))

        iface_type = detect_interface_type(raw_name)
        if raw_name.lower().startswith("eth-trunk"):
            iface_type = InterfaceType.PORT_CHANNEL
        if raw_name.lower().startswith("vlanif"):
            iface_type = InterfaceType.VLAN

        return Interface(
            name=raw_name,
            description=description,
            interface_type=iface_type,
            admin_status=enabled,
            status=InterfaceStatus.UP if enabled else InterfaceStatus.ADMIN_DOWN,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            prefix_length=prefix_length,
            secondary_ips=secondary_ips,
            mtu=mtu,
            speed=speed,
            duplex=duplex,
            switchport_mode=switchport_mode,
            access_vlan=access_vlan,
            trunk_vlans=trunk_vlans,
            vrf=vrf_name,
        )

    def _parse_vlans(self, raw_config: str) -> list[VLAN]:
        vlans: dict[int, VLAN] = {}
        for match in _RE_VLAN_BATCH.finditer(raw_config):
            for vlan_id in parse_vlan_range(match.group(1)):
                if vlan_id not in vlans:
                    vlans[vlan_id] = VLAN(vlan_id=vlan_id, name=f"VLAN{vlan_id:04d}")

        for match in _RE_VLAN_BLOCK.finditer(raw_config):
            vlan_id = int(match.group(1))
            block = match.group(2)
            name = None
            if m := _RE_VLAN_NAME.search(block):
                name = m.group(1).strip()
            description = None
            if m := _RE_VLAN_DESC.search(block):
                description = m.group(1).strip()
            vlans[vlan_id] = VLAN(vlan_id=vlan_id, name=name, description=description)

        return list(vlans.values())

    def _parse_static_routes(self, raw_config: str) -> list[Route]:
        routes: list[Route] = []
        for match in _RE_STATIC_ROUTE.finditer(raw_config):
            vrf_name, network, mask, next_hop, preference = match.groups()
            routes.append(
                Route(
                    network=f"{network}/{self._mask_to_prefix_length(mask)}",
                    prefix_length=self._mask_to_prefix_length(mask),
                    next_hop=next_hop,
                    protocol=RouteProtocol.STATIC,
                    admin_distance=int(preference) if preference else 60,
                    vrf=vrf_name,
                )
            )
        return routes

    def _parse_ospf(self, raw_config: str) -> list[OSPFProcess]:
        processes: list[OSPFProcess] = []
        for match in _RE_OSPF_PROCESS.finditer(raw_config):
            process_id = int(match.group(1))
            block = match.group(2)
            router_id = None
            if m := _RE_OSPF_ROUTER_ID.search(block):
                router_id = m.group(1)

            networks: list[OSPFNetwork] = []
            # Flat format: network <ip> <wildcard> area <area>
            for net in _RE_OSPF_NETWORK.finditer(block):
                ip, wildcard, area = net.groups()
                prefix = self._wildcard_to_prefix_length(wildcard)
                networks.append(OSPFNetwork(network=f"{ip}/{prefix}", wildcard=wildcard, area=area))
            # Nested format: area <id> block with network statements inside
            for area_m in _RE_OSPF_AREA_BLOCK.finditer(block):
                area_id = area_m.group(1)
                area_block = area_m.group(2)
                for net_m in _RE_OSPF_AREA_NETWORK.finditer(area_block):
                    ip, wildcard = net_m.groups()
                    prefix = self._wildcard_to_prefix_length(wildcard)
                    networks.append(OSPFNetwork(network=f"{ip}/{prefix}", wildcard=wildcard, area=area_id))
            processes.append(
                OSPFProcess(
                    process_id=process_id,
                    router_id=router_id,
                    networks=networks,
                )
            )
        return processes

    def _parse_bgp(self, raw_config: str) -> list[BGPProcess]:
        processes: list[BGPProcess] = []
        for match in _RE_BGP_PROCESS.finditer(raw_config):
            local_as = int(match.group(1))
            block = match.group(2)
            router_id = None
            if m := _RE_BGP_ROUTER_ID.search(block):
                router_id = m.group(1)

            descriptions: dict[str, str] = {
                m.group(1): m.group(2).strip() for m in _RE_BGP_PEER_DESC.finditer(block)
            }

            neighbors: list[BGPNeighbor] = []
            for peer in _RE_BGP_PEER.finditer(block):
                address, remote_as = peer.groups()
                neighbors.append(
                    BGPNeighbor(
                        address=address,
                        remote_as=int(remote_as),
                        description=descriptions.get(address),
                    )
                )

            processes.append(
                BGPProcess(
                    local_as=local_as,
                    router_id=router_id,
                    neighbors=neighbors,
                )
            )
        return processes

    def _parse_vrfs(self, raw_config: str) -> list[VRF]:
        vrfs: list[VRF] = []
        for match in _RE_VRF_BLOCK.finditer(raw_config):
            name = match.group(1)
            block = match.group(2)
            rd = None
            if m := _RE_VRF_RD.search(block):
                rd = m.group(1).strip()
            rt_import = [m.group(1).strip() for m in _RE_VRF_RT_IMPORT.finditer(block)]
            rt_export = [m.group(1).strip() for m in _RE_VRF_RT_EXPORT.finditer(block)]
            vrfs.append(VRF(name=name, rd=rd, rt_import=rt_import, rt_export=rt_export))
        return vrfs

    def _parse_acls(self, raw_config: str) -> list[ACL]:
        acls: list[ACL] = []
        for match in _RE_ACL_BASIC.finditer(raw_config):
            acl_name = match.group(1)
            block = match.group(2)
            description = _RE_ACL_DESC.search(block)
            acls.append(
                ACL(
                    name=acl_name,
                    acl_type=ACLType.IPV4_EXTENDED,
                    description=description.group(1).strip() if description else None,
                    entries=self._parse_acl_entries(block),
                )
            )

        for match in _RE_ACL_NAMED.finditer(raw_config):
            acl_name = match.group(1)
            block = match.group(2)
            description = _RE_ACL_DESC.search(block)
            acls.append(
                ACL(
                    name=acl_name,
                    acl_type=ACLType.NAMED_EXTENDED,
                    description=description.group(1).strip() if description else None,
                    entries=self._parse_acl_entries(block),
                )
            )
        return acls

    def _parse_acl_entries(self, block: str) -> list[ACLEntry]:
        entries: list[ACLEntry] = []
        for match in _RE_ACL_RULE.finditer(block):
            sequence = int(match.group(1))
            action = ACLAction.PERMIT if match.group(2) == "permit" else ACLAction.DENY
            protocol = match.group(3)
            rest = match.group(4)

            source = None
            destination = None
            if rest.startswith("source "):
                after_source = rest[len("source "):]
                if " destination " in after_source:
                    parts = after_source.split(" destination ", 1)
                    source = parts[0].strip()
                    destination = parts[1].strip()
                else:
                    tokens = after_source.split()
                    if len(tokens) >= 2:
                        source = tokens[0] + " " + tokens[1]
                        rest_tokens = tokens[2:]
                        if rest_tokens:
                            destination = " ".join(rest_tokens)
                    else:
                        source = after_source.strip()
            else:
                source = rest.strip()

            entries.append(
                ACLEntry(
                    sequence=sequence,
                    action=action,
                    protocol=protocol,
                    source=source,
                    destination=destination,
                )
            )
        return entries

    def _parse_nat(self, raw_config: str) -> list[NATRule]:
        rules: list[NATRule] = []
        for match in _RE_INTERFACE_BLOCK.finditer(raw_config):
            iface_name = match.group(1).strip()
            block = match.group(2)
            for nat_match in _RE_NAT_OUTBOUND.finditer(block):
                acl_id, address_group = nat_match.groups()
                rules.append(
                    NATRule(
                        rule_id=acl_id,
                        nat_type=NATType.DYNAMIC,
                        rule_type="outbound",
                        acl_name=acl_id,
                        address_group=address_group,
                        interface=iface_name,
                        translated_address=address_group,
                    )
                )
        return rules

    def _normalize_interface_name(self, name: str) -> str:
        """Normalize Huawei interface names to compact notation."""
        normalized = name.lower()
        normalized = normalized.replace("gigabitethernet", "ge")
        normalized = normalized.replace("eth-trunk", "et")
        normalized = normalized.replace("vlanif", "vl")
        normalized = normalized.replace("loopback", "lo")
        normalized = normalized.replace(" ", "")
        return normalized

    @staticmethod
    def _mask_to_prefix_length(mask: str) -> int:
        return sum(bin(int(octet)).count("1") for octet in mask.split("."))

    @staticmethod
    def _wildcard_to_prefix_length(wildcard: str) -> int:
        return 32 - sum(bin(int(octet)).count("1") for octet in wildcard.split("."))

    @staticmethod
    def _mask_to_wildcard(mask: str) -> str:
        return ".".join(str(255 - int(octet)) for octet in mask.split("."))
