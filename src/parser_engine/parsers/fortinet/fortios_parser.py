"""
Fortinet FortiOS configuration parser.

Supports:
  - Hostname (config system global → set hostname)
  - FortiOS version string
  - Interfaces (config system interface → edit <name>)
  - Static routes (config router static → edit <id>)
  - Firewall policies (config firewall policy → edit <id>)
  - Firewall addresses (used to resolve address objects)
  - NAT rules embedded in firewall policies (nat enable)

FortiOS uses a hierarchical indented-block syntax:
    config <section>
        edit <key>
            set <field> <value>
        next
    end
"""
from __future__ import annotations

import re
from typing import Optional

from ...models.device import Device, VendorType
from ...models.interface import Interface, InterfaceStatus, SwitchportMode, detect_interface_type
from ...models.routing import Route, RouteProtocol
from ...models.security import FirewallPolicy, FirewallPolicyAction, NATRule, NATType
from ..base_parser import BaseParser, ParserError

# ---------------------------------------------------------------------------
# Compiled regular expressions
# ---------------------------------------------------------------------------

_RE_HOSTNAME = re.compile(r'^\s+set hostname\s+"?([^"\n]+)"?', re.MULTILINE)
_RE_VERSION = re.compile(r"#config-version=\S+-(\d+\.\d+\.\d+)-", re.MULTILINE)
_RE_VERSION_ALT = re.compile(r"^#\s*FGT.*v(\d+\.\d+[\.\d]*)", re.MULTILINE | re.IGNORECASE)

# Section headers
_RE_CONFIG_SECTION = re.compile(r"^config\s+(.+)$", re.MULTILINE)
_RE_EDIT = re.compile(r"^\s+edit\s+(.+)$", re.MULTILINE)
_RE_SET = re.compile(r"^\s+set\s+(\S+)\s+(.*)", re.MULTILINE)
_RE_NEXT = re.compile(r"^\s+next\s*$", re.MULTILINE)
_RE_END = re.compile(r"^end\s*$", re.MULTILINE)


class FortiOSParser(BaseParser):
    """
    Parser for Fortinet FortiOS running configurations.

    FortiOS uses a nested ``config … edit … set … next … end`` syntax.
    This parser extracts top-level sections and iterates their entries.

    Example::

        parser = FortiOSParser()
        if parser.can_parse(config_text):
            result = await parser.parse(config_text)
            print(result.device.hostname)
    """

    vendor: VendorType = VendorType.FORTINET_FORTIOS
    parser_version: str = "1.0.0"

    _FORTIOS_FINGERPRINTS = (
        "config-version=fgt",
        "config-version=fmg",
        "config system global",
        "fortigate",
        "fortios",
        "#fgt",
    )

    # ------------------------------------------------------------------
    # BaseParser interface
    # ------------------------------------------------------------------

    def can_parse(self, raw_config: str) -> bool:
        """
        Return True when the config looks like a FortiOS backup / running-config.

        Args:
            raw_config: Full configuration text.

        Returns:
            True for FortiOS configurations.
        """
        header = "\n".join(raw_config.splitlines()[:30]).lower()
        return any(fp in header for fp in self._FORTIOS_FINGERPRINTS)

    async def _do_parse(self, raw_config: str) -> Device:
        """
        Parse a FortiOS configuration and return a Device.

        Args:
            raw_config: Full configuration text.

        Returns:
            Populated Device model.
        """
        hostname = self._parse_hostname(raw_config)
        os_version = self._parse_version(raw_config)
        sections = self._split_sections(raw_config)

        interfaces = self._parse_interfaces(sections.get("system interface", ""))
        static_routes = self._parse_static_routes(sections.get("router static", ""))
        firewall_policies = self._parse_firewall_policies(
            sections.get("firewall policy", "")
        )
        nat_rules = self._extract_nat_from_policies(firewall_policies)

        return Device(
            hostname=hostname,
            vendor=self.vendor,
            os_version=os_version,
            interfaces=interfaces,
            static_routes=static_routes,
            firewall_policies=firewall_policies,
            nat_rules=nat_rules,
            raw_config=raw_config,
        )

    # ------------------------------------------------------------------
    # Section parsing
    # ------------------------------------------------------------------

    def _parse_hostname(self, config: str) -> str:
        """Extract hostname from 'config system global' block."""
        match = _RE_HOSTNAME.search(config)
        if not match:
            self._warn("Hostname not found in FortiOS config; using 'unknown'")
            return "unknown"
        return match.group(1).strip()

    def _parse_version(self, config: str) -> Optional[str]:
        """Extract FortiOS version from the config-version comment line."""
        match = _RE_VERSION.search(config) or _RE_VERSION_ALT.search(config)
        return match.group(1) if match else None

    def _split_sections(self, config: str) -> dict[str, str]:
        """
        Split the configuration into top-level ``config <section>`` blocks.

        Args:
            config: Full configuration text.

        Returns:
            Mapping of section name → section text.
        """
        sections: dict[str, str] = {}
        section_matches = list(_RE_CONFIG_SECTION.finditer(config))

        for idx, match in enumerate(section_matches):
            section_name = match.group(1).strip().lower()
            start = match.start()
            # End at the next top-level 'config' or EOF
            end = section_matches[idx + 1].start() if idx + 1 < len(section_matches) else len(config)
            sections[section_name] = config[start:end]

        return sections

    def _parse_entries(self, section_text: str) -> list[dict[str, str]]:
        """
        Parse all ``edit … next`` entries in a section into key→value dicts.

        Args:
            section_text: Text of a single config section.

        Returns:
            List of dicts, one per edit block.
        """
        entries: list[dict[str, str]] = []
        current: dict[str, str] = {}
        inside_edit = False

        for line in section_text.splitlines():
            stripped = line.strip()

            edit_match = re.match(r"^edit\s+(.*)", stripped)
            if edit_match:
                current = {"_edit_key": edit_match.group(1).strip().strip('"')}
                inside_edit = True
                continue

            if stripped == "next" and inside_edit:
                entries.append(current)
                current = {}
                inside_edit = False
                continue

            if inside_edit:
                set_match = re.match(r"^set\s+(\S+)\s+(.*)", stripped)
                if set_match:
                    current[set_match.group(1)] = set_match.group(2).strip().strip('"')

        return entries

    # ------------------------------------------------------------------
    # Interfaces
    # ------------------------------------------------------------------

    def _parse_interfaces(self, section_text: str) -> list[Interface]:
        """Parse 'config system interface' entries."""
        interfaces: list[Interface] = []
        if not section_text:
            return interfaces

        for entry in self._parse_entries(section_text):
            try:
                iface = self._build_interface(entry)
                interfaces.append(iface)
            except Exception as exc:
                name = entry.get("_edit_key", "?")
                self._warn(f"Failed to parse FortiOS interface '{name}': {exc}")

        return interfaces

    def _build_interface(self, entry: dict[str, str]) -> Interface:
        """Build an Interface from a parsed FortiOS interface entry dict."""
        name = entry.get("_edit_key", "unknown")
        iface_type = detect_interface_type(name)

        # IP address (FortiOS format: "x.x.x.x y.y.y.y")
        ip_address: Optional[str] = None
        subnet_mask: Optional[str] = None
        ip_raw = entry.get("ip", "")
        if ip_raw and ip_raw not in ("0.0.0.0 0.0.0.0", ""):
            parts = ip_raw.split()
            if len(parts) >= 1:
                ip_address = parts[0]
            if len(parts) >= 2:
                subnet_mask = parts[1]

        # Admin status
        status_raw = entry.get("status", "up").lower()
        admin_status = status_raw != "down"
        status = InterfaceStatus.ADMIN_DOWN if not admin_status else InterfaceStatus.UNKNOWN

        # Description / alias
        description = entry.get("alias") or entry.get("description") or None

        # Speed / MTU
        speed_raw = entry.get("speed", "")
        speed: Optional[int] = None
        if speed_raw.isdigit():
            speed = int(speed_raw)

        mtu_raw = entry.get("mtu", "")
        mtu: Optional[int] = int(mtu_raw) if mtu_raw.isdigit() else None

        # VRF / VDOM (FortiOS uses VDOM, mapped to vrf field)
        vrf = entry.get("vdom") or None

        # VLAN (FortiOS 'vlanid' field)
        access_vlan: Optional[int] = None
        vlanid_raw = entry.get("vlanid", "")
        if vlanid_raw.isdigit():
            access_vlan = int(vlanid_raw)
            # Re-classify as VLAN interface type if vlanid is set
            from ...models.interface import InterfaceType
            iface_type = InterfaceType.VLAN

        return Interface(
            name=name,
            description=description,
            interface_type=iface_type,
            admin_status=admin_status,
            status=status,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            speed=speed,
            mtu=mtu,
            vrf=vrf,
            access_vlan=access_vlan,
            switchport_mode=SwitchportMode.ROUTED,
        )

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _parse_static_routes(self, section_text: str) -> list[Route]:
        """Parse 'config router static' entries."""
        routes: list[Route] = []
        if not section_text:
            return routes

        for entry in self._parse_entries(section_text):
            try:
                route = self._build_static_route(entry)
                if route:
                    routes.append(route)
            except Exception as exc:
                self._warn(f"Failed to parse FortiOS static route: {exc}")

        return routes

    def _build_static_route(self, entry: dict[str, str]) -> Optional[Route]:
        """Build a Route from a parsed FortiOS static route entry."""
        dst = entry.get("dst", "")
        if not dst or dst in ("0.0.0.0 0.0.0.0",):
            return None

        parts = dst.split()
        network = parts[0]
        mask = parts[1] if len(parts) > 1 else None

        gateway = entry.get("gateway") or None
        device = entry.get("device") or None
        distance_raw = entry.get("distance", "")
        distance = int(distance_raw) if distance_raw.isdigit() else None

        return Route(
            network=network,
            subnet_mask=mask,
            next_hop=gateway,
            exit_interface=device,
            admin_distance=distance,
            protocol=RouteProtocol.STATIC,
        )

    # ------------------------------------------------------------------
    # Firewall policies
    # ------------------------------------------------------------------

    def _parse_firewall_policies(self, section_text: str) -> list[FirewallPolicy]:
        """Parse 'config firewall policy' entries."""
        policies: list[FirewallPolicy] = []
        if not section_text:
            return policies

        for entry in self._parse_entries(section_text):
            try:
                policy = self._build_firewall_policy(entry)
                policies.append(policy)
            except Exception as exc:
                pid = entry.get("_edit_key", "?")
                self._warn(f"Failed to parse FortiOS policy {pid}: {exc}")

        return policies

    def _build_firewall_policy(self, entry: dict[str, str]) -> FirewallPolicy:
        """Build a FirewallPolicy from a parsed FortiOS policy entry."""
        policy_id = int(entry.get("_edit_key", "0"))

        action_raw = entry.get("action", "deny").lower()
        action_map = {
            "accept": FirewallPolicyAction.ACCEPT,
            "deny": FirewallPolicyAction.DENY,
            "drop": FirewallPolicyAction.DROP,
        }
        action = action_map.get(action_raw, FirewallPolicyAction.DENY)

        status_raw = entry.get("status", "enable").lower()
        status = status_raw == "enable"

        nat_raw = entry.get("nat", "disable").lower()
        nat = nat_raw == "enable"

        logtraffic = entry.get("logtraffic", "disable").lower()
        logging = logtraffic in ("all", "utm")

        # Multi-value fields (FortiOS stores them space-separated in quotes)
        def _split_multivalue(raw: str) -> list[str]:
            return [v.strip().strip('"') for v in raw.split() if v.strip()] if raw else []

        src_intf = _split_multivalue(entry.get("srcintf", ""))
        dst_intf = _split_multivalue(entry.get("dstintf", ""))
        src_addr = _split_multivalue(entry.get("srcaddr", ""))
        dst_addr = _split_multivalue(entry.get("dstaddr", ""))
        services = _split_multivalue(entry.get("service", ""))

        return FirewallPolicy(
            policy_id=policy_id,
            name=entry.get("name"),
            source_zones=src_intf,
            destination_zones=dst_intf,
            source_addresses=src_addr,
            destination_addresses=dst_addr,
            services=services,
            action=action,
            nat=nat,
            logging=logging,
            status=status,
            schedule=entry.get("schedule"),
            comments=entry.get("comments"),
        )

    def _extract_nat_from_policies(
        self, policies: list[FirewallPolicy]
    ) -> list[NATRule]:
        """
        Derive NATRule entries from firewall policies that have NAT enabled.

        FortiOS does not have a separate NAT table for policy-based NAT;
        it is a flag on the firewall policy itself.

        Args:
            policies: Parsed firewall policies.

        Returns:
            List of NATRule objects derived from NAT-enabled policies.
        """
        nat_rules: list[NATRule] = []
        for policy in policies:
            if policy.nat:
                nat_rules.append(
                    NATRule(
                        rule_id=f"policy_{policy.policy_id}",
                        nat_type=NATType.POLICY,
                        source_network=", ".join(policy.source_addresses) or None,
                        interface=(
                            policy.destination_zones[0]
                            if policy.destination_zones
                            else None
                        ),
                    )
                )
        return nat_rules
