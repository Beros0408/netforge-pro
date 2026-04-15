"""
Cisco IOS / IOS-XE configuration parser.

Supports:
  - Hostname detection
  - IOS version string
  - Interfaces (L2 and L3, with IP, description, shutdown, VLANs)
  - VLANs (database and interface-level)
  - Static routes (ip route)
  - OSPF (router ospf)
  - BGP (router bgp)
  - Numbered and named ACLs (standard and extended)
  - NAT rules (ip nat inside source)
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
)
from ...models.security import ACL, ACLEntry, ACLAction, ACLType, NATRule, NATType
from ..base_parser import BaseParser, ParserError

# ---------------------------------------------------------------------------
# Compiled regular expressions
# ---------------------------------------------------------------------------

_RE_HOSTNAME = re.compile(r"^hostname\s+(\S+)", re.MULTILINE)
_RE_VERSION = re.compile(r"^version\s+(\S+)", re.MULTILINE)
_RE_INTERFACE_HEADER = re.compile(r"^interface\s+(\S+)", re.MULTILINE)
_RE_IP_ADDRESS = re.compile(
    r"^\s+ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)(\s+secondary)?",
    re.MULTILINE,
)
_RE_IPV6_ADDRESS = re.compile(
    r"^\s+ipv6 address\s+([0-9a-fA-F:]+/\d+)", re.MULTILINE
)
_RE_DESCRIPTION = re.compile(r"^\s+description\s+(.*)", re.MULTILINE)
_RE_SHUTDOWN = re.compile(r"^\s+shutdown\s*$", re.MULTILINE)
_RE_SPEED = re.compile(r"^\s+speed\s+(\d+)", re.MULTILINE)
_RE_DUPLEX = re.compile(r"^\s+duplex\s+(\S+)", re.MULTILINE)
_RE_MTU = re.compile(r"^\s+mtu\s+(\d+)", re.MULTILINE)
_RE_VRF_FWD = re.compile(r"^\s+ip vrf forwarding\s+(\S+)", re.MULTILINE)
_RE_VRF_MEMBER = re.compile(r"^\s+vrf member\s+(\S+)", re.MULTILINE)

# Layer-2
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
_RE_CHANNEL_GROUP = re.compile(r"^\s+channel-group\s+(\d+)", re.MULTILINE)

# VLANs
_RE_VLAN_HEADER = re.compile(r"^vlan\s+([\d,\-]+)\s*$", re.MULTILINE)
_RE_VLAN_NAME = re.compile(r"^\s+name\s+(\S+)", re.MULTILINE)
_RE_VLAN_STATE = re.compile(r"^\s+state\s+(\S+)", re.MULTILINE)

# Routing
_RE_IP_ROUTE = re.compile(
    r"^ip route(?:\s+vrf\s+(\S+))?\s+"
    r"(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)"
    r"(?:\s+(\S+))?"
    r"(?:\s+(\d+))?",
    re.MULTILINE,
)
_RE_OSPF_HEADER = re.compile(r"^router ospf\s+(\d+)(?:\s+vrf\s+(\S+))?", re.MULTILINE)
_RE_OSPF_ROUTER_ID = re.compile(r"^\s+router-id\s+(\S+)", re.MULTILINE)
_RE_OSPF_NETWORK = re.compile(
    r"^\s+network\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+area\s+(\S+)",
    re.MULTILINE,
)
_RE_OSPF_PASSIVE = re.compile(r"^\s+passive-interface\s+(\S+)", re.MULTILINE)
_RE_OSPF_REDIST = re.compile(
    r"^\s+redistribute\s+(\S+)(?:\s+metric\s+(\d+))?(?:\s+metric-type\s+([12]))?",
    re.MULTILINE,
)

_RE_BGP_HEADER = re.compile(r"^router bgp\s+(\d+)", re.MULTILINE)
_RE_BGP_ROUTER_ID = re.compile(r"^\s+bgp router-id\s+(\S+)", re.MULTILINE)
_RE_BGP_NEIGHBOR = re.compile(r"^\s+neighbor\s+(\S+)\s+remote-as\s+(\d+)", re.MULTILINE)
_RE_BGP_NEIGHBOR_DESC = re.compile(r"^\s+neighbor\s+(\S+)\s+description\s+(.*)", re.MULTILINE)
_RE_BGP_NEIGHBOR_UPDATE_SRC = re.compile(
    r"^\s+neighbor\s+(\S+)\s+update-source\s+(\S+)", re.MULTILINE
)
_RE_BGP_NEIGHBOR_NH_SELF = re.compile(
    r"^\s+neighbor\s+(\S+)\s+next-hop-self", re.MULTILINE
)
_RE_BGP_NEIGHBOR_RM_IN = re.compile(
    r"^\s+neighbor\s+(\S+)\s+route-map\s+(\S+)\s+in", re.MULTILINE
)
_RE_BGP_NEIGHBOR_RM_OUT = re.compile(
    r"^\s+neighbor\s+(\S+)\s+route-map\s+(\S+)\s+out", re.MULTILINE
)
_RE_BGP_NETWORK = re.compile(
    r"^\s+network\s+(\d+\.\d+\.\d+\.\d+)(?:\s+mask\s+(\d+\.\d+\.\d+\.\d+))?",
    re.MULTILINE,
)

# ACLs
_RE_STANDARD_ACL = re.compile(
    r"^access-list\s+(\d+)\s+(permit|deny)\s+(.*)", re.MULTILINE
)
_RE_EXTENDED_ACL = re.compile(
    r"^access-list\s+(1[0-9]{2})\s+(permit|deny)\s+(\S+)\s+(.*)",
    re.MULTILINE,
)
_RE_NAMED_ACL_HEADER = re.compile(
    r"^ip access-list\s+(standard|extended)\s+(\S+)", re.MULTILINE
)
_RE_NAMED_ACL_ENTRY = re.compile(
    r"^\s+(?:(\d+)\s+)?(permit|deny|remark)\s+(.*)", re.MULTILINE
)

# NAT
_RE_NAT_INSIDE_SOURCE_STATIC = re.compile(
    r"^ip nat inside source static\s+(\S+)\s+(\S+)", re.MULTILINE
)
_RE_NAT_INSIDE_SOURCE_LIST = re.compile(
    r"^ip nat inside source list\s+(\S+)\s+(?:pool\s+(\S+)|interface\s+(\S+))(?:\s+overload)?",
    re.MULTILINE,
)

# Splitter — section boundary used to isolate config stanzas
_RE_SECTION_START = re.compile(
    r"^(?:interface|router|vlan|ip access-list|line)\s+\S+", re.MULTILINE
)


class CiscoIOSParser(BaseParser):
    """
    Parser for Cisco IOS and IOS-XE running configurations.

    Identifies device attributes, interfaces, VLANs, routing protocols,
    ACLs and NAT rules from the flat text of a Cisco IOS running-config.

    Example::

        parser = CiscoIOSParser()
        if parser.can_parse(config_text):
            result = await parser.parse(config_text)
            print(result.device.hostname)
    """

    vendor: VendorType = VendorType.CISCO_IOS
    parser_version: str = "1.0.0"

    # Keywords that appear near the top of a genuine Cisco IOS config
    _CISCO_FINGERPRINTS = (
        "cisco ios",
        "cisco ios-xe",
        "building configuration",
        "current configuration",
        "ios software",
    )

    # ------------------------------------------------------------------
    # BaseParser interface
    # ------------------------------------------------------------------

    def can_parse(self, raw_config: str) -> bool:
        """
        Return True when the config looks like a Cisco IOS running-config.

        Checks the first 30 lines for well-known Cisco strings.

        Args:
            raw_config: Full configuration text.

        Returns:
            True for Cisco IOS / IOS-XE configurations.
        """
        header = "\n".join(raw_config.splitlines()[:30]).lower()
        return any(fp in header for fp in self._CISCO_FINGERPRINTS)

    async def _do_parse(self, raw_config: str) -> Device:
        """
        Parse a Cisco IOS running-config and return a Device.

        Args:
            raw_config: Full configuration text.

        Returns:
            Populated Device model.
        """
        hostname = self._parse_hostname(raw_config)
        os_version = self._parse_version(raw_config)
        interfaces = self._parse_interfaces(raw_config)
        vlans = self._parse_vlans(raw_config)
        static_routes = self._parse_static_routes(raw_config)
        ospf_processes = self._parse_ospf(raw_config)
        bgp_processes = self._parse_bgp(raw_config)
        acls = self._parse_acls(raw_config)
        nat_rules = self._parse_nat(raw_config)

        return Device(
            hostname=hostname,
            vendor=self.vendor,
            os_version=os_version,
            interfaces=interfaces,
            vlans=vlans,
            static_routes=static_routes,
            ospf_processes=ospf_processes,
            bgp_processes=bgp_processes,
            acls=acls,
            nat_rules=nat_rules,
            raw_config=raw_config,
        )

    # ------------------------------------------------------------------
    # Private parsing helpers
    # ------------------------------------------------------------------

    def _parse_hostname(self, config: str) -> str:
        """Extract the hostname from the configuration."""
        match = _RE_HOSTNAME.search(config)
        if not match:
            self._warn("Hostname not found; using 'unknown'")
            return "unknown"
        return match.group(1)

    def _parse_version(self, config: str) -> Optional[str]:
        """Extract the IOS version string."""
        match = _RE_VERSION.search(config)
        return match.group(1) if match else None

    def _parse_interfaces(self, config: str) -> list[Interface]:
        """
        Parse all interface stanzas from the configuration.

        Returns:
            List of Interface objects.
        """
        interfaces: list[Interface] = []

        # Locate each "interface <name>" header and its body
        headers = list(_RE_INTERFACE_HEADER.finditer(config))
        for idx, header in enumerate(headers):
            iface_name = header.group(1)
            start = header.start()
            # Body ends at the next top-level keyword or EOF
            end = headers[idx + 1].start() if idx + 1 < len(headers) else len(config)
            block = config[start:end]

            try:
                iface = self._parse_interface_block(iface_name, block)
                interfaces.append(iface)
            except Exception as exc:
                self._warn(f"Failed to parse interface {iface_name}: {exc}")

        return interfaces

    def _parse_interface_block(self, name: str, block: str) -> Interface:
        """Parse a single interface block into an Interface model."""
        iface_type = detect_interface_type(name)
        admin_status = not bool(_RE_SHUTDOWN.search(block))
        status = InterfaceStatus.ADMIN_DOWN if not admin_status else InterfaceStatus.UNKNOWN

        # Primary IP
        ip_address: Optional[str] = None
        subnet_mask: Optional[str] = None
        secondary_ips: list[str] = []

        for m in _RE_IP_ADDRESS.finditer(block):
            if m.group(3):  # secondary keyword
                secondary_ips.append(m.group(1))
            else:
                ip_address = m.group(1)
                subnet_mask = m.group(2)

        # Description
        desc_match = _RE_DESCRIPTION.search(block)
        description = desc_match.group(1).strip() if desc_match else None

        # Speed / duplex / MTU
        speed_match = _RE_SPEED.search(block)
        speed = int(speed_match.group(1)) if speed_match else None

        duplex_match = _RE_DUPLEX.search(block)
        duplex = duplex_match.group(1) if duplex_match else None

        mtu_match = _RE_MTU.search(block)
        mtu = int(mtu_match.group(1)) if mtu_match else None

        # VRF
        vrf_match = _RE_VRF_FWD.search(block) or _RE_VRF_MEMBER.search(block)
        vrf = vrf_match.group(1) if vrf_match else None

        # Layer-2
        switchport_mode = SwitchportMode.ROUTED
        access_vlan: Optional[int] = None
        trunk_vlans: list[int] = []
        native_vlan: Optional[int] = None

        mode_match = _RE_SWITCHPORT_MODE.search(block)
        if mode_match:
            raw_mode = mode_match.group(1).lower()
            mode_map = {
                "access": SwitchportMode.ACCESS,
                "trunk": SwitchportMode.TRUNK,
                "dynamic desirable": SwitchportMode.TRUNK,
                "dynamic auto": SwitchportMode.TRUNK,
            }
            switchport_mode = mode_map.get(raw_mode, SwitchportMode.UNKNOWN)

        access_vlan_match = _RE_SWITCHPORT_ACCESS_VLAN.search(block)
        if access_vlan_match:
            access_vlan = int(access_vlan_match.group(1))
            if switchport_mode == SwitchportMode.ROUTED:
                switchport_mode = SwitchportMode.ACCESS

        trunk_allowed_match = _RE_SWITCHPORT_TRUNK_ALLOWED.search(block)
        if trunk_allowed_match:
            try:
                trunk_vlans = parse_vlan_range(trunk_allowed_match.group(1))
            except ValueError as exc:
                self._warn(f"Interface {name}: invalid trunk VLAN range — {exc}")

        native_vlan_match = _RE_SWITCHPORT_TRUNK_NATIVE.search(block)
        if native_vlan_match:
            native_vlan = int(native_vlan_match.group(1))

        # Port-channel
        channel_match = _RE_CHANNEL_GROUP.search(block)
        channel_group = int(channel_match.group(1)) if channel_match else None

        return Interface(
            name=name,
            description=description,
            interface_type=iface_type,
            admin_status=admin_status,
            status=status,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            secondary_ips=secondary_ips,
            speed=speed,
            duplex=duplex,
            mtu=mtu,
            vrf=vrf,
            switchport_mode=switchport_mode,
            access_vlan=access_vlan,
            trunk_vlans=trunk_vlans,
            native_vlan=native_vlan,
            channel_group=channel_group,
        )

    def _parse_vlans(self, config: str) -> list[VLAN]:
        """Parse VLAN database stanzas."""
        vlans: dict[int, VLAN] = {}

        # Locate all "vlan <id(s)>" top-level blocks
        vlan_headers = list(_RE_VLAN_HEADER.finditer(config))
        for idx, header in enumerate(vlan_headers):
            start = header.start()
            end = vlan_headers[idx + 1].start() if idx + 1 < len(vlan_headers) else len(config)
            block = config[start:end]

            try:
                vlan_ids = parse_vlan_range(header.group(1))
            except ValueError:
                continue

            name_match = _RE_VLAN_NAME.search(block)
            state_match = _RE_VLAN_STATE.search(block)

            vlan_name = name_match.group(1) if name_match else None
            state_str = state_match.group(1).lower() if state_match else "active"
            status = VLANStatus.SUSPEND if state_str == "suspend" else VLANStatus.ACTIVE

            for vid in vlan_ids:
                vlans[vid] = VLAN(vlan_id=vid, name=vlan_name, status=status)

        return list(vlans.values())

    def _parse_static_routes(self, config: str) -> list[Route]:
        """Parse all 'ip route' statements."""
        routes: list[Route] = []
        for match in _RE_IP_ROUTE.finditer(config):
            vrf = match.group(1)
            network = match.group(2)
            mask = match.group(3)
            next_hop_or_iface = match.group(4)
            metric_str = match.group(5)

            # Determine if group(4) is a next-hop IP or interface name
            next_hop: Optional[str] = None
            exit_iface: Optional[str] = None
            if next_hop_or_iface:
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", next_hop_or_iface):
                    next_hop = next_hop_or_iface
                else:
                    exit_iface = next_hop_or_iface

            routes.append(
                Route(
                    network=network,
                    subnet_mask=mask,
                    next_hop=next_hop,
                    exit_interface=exit_iface,
                    metric=int(metric_str) if metric_str else None,
                    protocol=RouteProtocol.STATIC,
                    vrf=vrf,
                )
            )
        return routes

    def _parse_ospf(self, config: str) -> list[OSPFProcess]:
        """Parse all 'router ospf' blocks."""
        processes: list[OSPFProcess] = []
        ospf_headers = list(_RE_OSPF_HEADER.finditer(config))
        all_section_starts = list(_RE_SECTION_START.finditer(config))

        for header in ospf_headers:
            pid = int(header.group(1))
            vrf = header.group(2)
            block = self._extract_block(config, header.start(), all_section_starts)

            router_id_match = _RE_OSPF_ROUTER_ID.search(block)
            router_id = router_id_match.group(1) if router_id_match else None

            networks = [
                OSPFNetwork(
                    network=m.group(1),
                    wildcard=m.group(2),
                    area=m.group(3),
                )
                for m in _RE_OSPF_NETWORK.finditer(block)
            ]

            passive = [m.group(1) for m in _RE_OSPF_PASSIVE.finditer(block)]

            redistributions = [
                OSPFRedistribution(
                    source_protocol=m.group(1),
                    metric=int(m.group(2)) if m.group(2) else None,
                    metric_type=int(m.group(3)) if m.group(3) else None,
                )
                for m in _RE_OSPF_REDIST.finditer(block)
            ]

            processes.append(
                OSPFProcess(
                    process_id=pid,
                    router_id=router_id,
                    networks=networks,
                    passive_interfaces=passive,
                    redistributions=redistributions,
                    vrf=vrf,
                )
            )

        return processes

    def _parse_bgp(self, config: str) -> list[BGPProcess]:
        """Parse all 'router bgp' blocks."""
        processes: list[BGPProcess] = []
        bgp_headers = list(_RE_BGP_HEADER.finditer(config))
        all_section_starts = list(_RE_SECTION_START.finditer(config))

        for header in bgp_headers:
            local_as = int(header.group(1))
            block = self._extract_block(config, header.start(), all_section_starts)

            router_id_match = _RE_BGP_ROUTER_ID.search(block)
            router_id = router_id_match.group(1) if router_id_match else None

            # Build neighbor objects
            neighbors: dict[str, BGPNeighbor] = {}
            for m in _RE_BGP_NEIGHBOR.finditer(block):
                addr, remote_as = m.group(1), int(m.group(2))
                neighbors[addr] = BGPNeighbor(address=addr, remote_as=remote_as)

            for m in _RE_BGP_NEIGHBOR_DESC.finditer(block):
                addr = m.group(1)
                if addr in neighbors:
                    neighbors[addr].description = m.group(2).strip()

            for m in _RE_BGP_NEIGHBOR_UPDATE_SRC.finditer(block):
                addr = m.group(1)
                if addr in neighbors:
                    neighbors[addr].update_source = m.group(2)

            for m in _RE_BGP_NEIGHBOR_NH_SELF.finditer(block):
                addr = m.group(1)
                if addr in neighbors:
                    neighbors[addr].next_hop_self = True

            for m in _RE_BGP_NEIGHBOR_RM_IN.finditer(block):
                addr = m.group(1)
                if addr in neighbors:
                    neighbors[addr].route_map_in = m.group(2)

            for m in _RE_BGP_NEIGHBOR_RM_OUT.finditer(block):
                addr = m.group(1)
                if addr in neighbors:
                    neighbors[addr].route_map_out = m.group(2)

            networks = [
                BGPNetwork(network=m.group(1), mask=m.group(2))
                for m in _RE_BGP_NETWORK.finditer(block)
            ]

            processes.append(
                BGPProcess(
                    local_as=local_as,
                    router_id=router_id,
                    neighbors=list(neighbors.values()),
                    networks=networks,
                )
            )

        return processes

    def _parse_acls(self, config: str) -> list[ACL]:
        """Parse numbered and named ACLs."""
        acls: dict[str, ACL] = {}

        # Standard numbered ACLs (1-99, 1300-1999)
        for m in _RE_STANDARD_ACL.finditer(config):
            num = m.group(1)
            int_num = int(num)
            if (1 <= int_num <= 99) or (1300 <= int_num <= 1999):
                if num not in acls:
                    acls[num] = ACL(name=num, acl_type=ACLType.STANDARD)
                action = ACLAction(m.group(2))
                acls[num].entries.append(
                    ACLEntry(action=action, source=m.group(3).strip())
                )

        # Extended numbered ACLs (100-199, 2000-2699)
        for m in _RE_EXTENDED_ACL.finditer(config):
            num = m.group(1)
            if num not in acls:
                acls[num] = ACL(name=num, acl_type=ACLType.NAMED_EXTENDED)
            action = ACLAction(m.group(2))
            protocol = m.group(3)
            rest = m.group(4).strip()
            # Rudimentary src/dst split
            parts = rest.split()
            source = parts[0] if parts else None
            destination = parts[1] if len(parts) > 1 else None
            acls[num].entries.append(
                ACLEntry(action=action, protocol=protocol, source=source, destination=destination)
            )

        # Named ACLs
        named_headers = list(_RE_NAMED_ACL_HEADER.finditer(config))
        all_section_starts = list(_RE_SECTION_START.finditer(config))

        for header in named_headers:
            acl_type_str = header.group(1).lower()
            name = header.group(2)
            acl_type = (
                ACLType.NAMED_STANDARD if acl_type_str == "standard" else ACLType.NAMED_EXTENDED
            )
            block = self._extract_block(config, header.start(), all_section_starts)

            acl = ACL(name=name, acl_type=acl_type)
            for m in _RE_NAMED_ACL_ENTRY.finditer(block):
                seq = int(m.group(1)) if m.group(1) else None
                keyword = m.group(2).lower()
                rest = m.group(3).strip()

                if keyword == "remark":
                    acl.entries.append(ACLEntry(action=ACLAction.PERMIT, remark=rest, sequence=seq))
                    continue

                action = ACLAction(keyword)
                parts = rest.split()
                protocol = parts[0] if parts else None
                remaining = parts[1:] if len(parts) > 1 else []
                source = remaining[0] if remaining else None
                destination = remaining[1] if len(remaining) > 1 else None

                acl.entries.append(
                    ACLEntry(
                        sequence=seq,
                        action=action,
                        protocol=protocol,
                        source=source,
                        destination=destination,
                    )
                )

            acls[name] = acl

        return list(acls.values())

    def _parse_nat(self, config: str) -> list[NATRule]:
        """Parse ip nat inside source rules."""
        rules: list[NATRule] = []

        for idx, m in enumerate(_RE_NAT_INSIDE_SOURCE_STATIC.finditer(config)):
            rules.append(
                NATRule(
                    rule_id=f"static_{idx}",
                    nat_type=NATType.STATIC,
                    source_network=m.group(1),
                    translated_address=m.group(2),
                )
            )

        for idx, m in enumerate(_RE_NAT_INSIDE_SOURCE_LIST.finditer(config)):
            pool_or_iface = m.group(2) or m.group(3)
            overload = "overload" in config[m.start():m.end() + 20]
            rules.append(
                NATRule(
                    rule_id=f"list_{m.group(1)}",
                    nat_type=NATType.PAT if overload else NATType.DYNAMIC,
                    acl_name=m.group(1),
                    translated_address=pool_or_iface if m.group(2) else None,
                    interface=m.group(3),
                    overload=overload,
                )
            )

        return rules

    # ------------------------------------------------------------------
    # Internal utility
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_block(
        config: str,
        start: int,
        section_starts: list[re.Match],  # type: ignore[type-arg]
    ) -> str:
        """
        Extract the text of a configuration block starting at *start*.

        Ends at the next top-level section or EOF.

        Args:
            config: Full configuration text.
            start: Character offset of the block header.
            section_starts: Pre-computed list of all top-level section match objects.

        Returns:
            Block text as a string.
        """
        for sec in section_starts:
            if sec.start() > start:
                return config[start : sec.start()]
        return config[start:]
