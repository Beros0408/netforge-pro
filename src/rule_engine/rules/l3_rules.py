"""
Layer 3 rules — OSPF, BGP, VRF, and routing checks.
"""
from __future__ import annotations

import ipaddress
from typing import List, Optional

from ...parser_engine.models.device import Device
from ..models.problem import Category, Problem, Severity
from .base_rule import BaseRule


class OSPFAreaMismatchRule(BaseRule):
    """
    L3_OSPF_001 — Same network prefix advertised in different OSPF areas
    across devices.  OSPF neighbors won't form adjacency when areas differ.
    """

    rule_id = "L3_OSPF_001"
    title = "OSPF area mismatch"
    category = Category.L3
    severity = Severity.HIGH

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        # {network: {area: [(hostname, process_id)]}}
        network_areas: dict[str, dict[str, list]] = {}

        for device in devices:
            for proc in device.ospf_processes:
                for net in proc.networks:
                    network_areas.setdefault(net.network, {}).setdefault(
                        net.area, []
                    ).append((device.hostname, proc.process_id))

        for network, area_map in network_areas.items():
            if len(area_map) <= 1:
                continue
            all_areas = sorted(area_map.keys())
            for area, entries in area_map.items():
                for dev_hostname, proc_id in entries:
                    problems.append(self._make_problem(
                        device_hostname=dev_hostname,
                        title="OSPF area mismatch for network",
                        description=(
                            f"Network {network} appears in OSPF area {area} "
                            f"on '{dev_hostname}' but in area(s) "
                            f"{[a for a in all_areas if a != area]} on other devices."
                        ),
                        impact=(
                            "OSPF neighbors sharing this subnet will not form "
                            "adjacency, causing routing failure."
                        ),
                        recommendation=(
                            f"Ensure network {network} is configured in the "
                            "same area on all adjacent devices."
                        ),
                        evidence={
                            "network": network,
                            "this_area": area,
                            "all_areas": all_areas,
                            "ospf_process_id": proc_id,
                        },
                    ))

        return problems


class OSPFMTUMismatchRule(BaseRule):
    """
    L3_OSPF_002 — Interfaces in the same OSPF area with different MTU values.
    OSPF adjacency gets stuck in EXSTART/EXCHANGE when MTU differs.
    """

    rule_id = "L3_OSPF_002"
    title = "MTU mismatch between OSPF neighbors"
    category = Category.L3
    severity = Severity.HIGH

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        # {area: [(hostname, iface_name, mtu, network)]}
        area_entries: dict[str, list] = {}

        for device in devices:
            for proc in device.ospf_processes:
                for net_stmt in proc.networks:
                    for iface in device.interfaces:
                        if iface.ip_address and iface.mtu and self._matches(
                            iface.ip_address, net_stmt.network, net_stmt.wildcard
                        ):
                            area_entries.setdefault(net_stmt.area, []).append(
                                (device.hostname, iface.name, iface.mtu, net_stmt.network)
                            )

        for area, entries in area_entries.items():
            mtus = {e[2] for e in entries}
            if len(mtus) <= 1:
                continue
            for dev_hostname, iface_name, mtu, network in entries:
                problems.append(self._make_problem(
                    device_hostname=dev_hostname,
                    interface=iface_name,
                    title="OSPF MTU mismatch in area",
                    description=(
                        f"Interface {iface_name} (MTU {mtu}) is in OSPF area {area}, "
                        f"but other interfaces in the same area have MTU(s) "
                        f"{sorted(mtus - {mtu})}."
                    ),
                    impact=(
                        "OSPF adjacency will stall at EXSTART/EXCHANGE state "
                        "when MTU values differ between neighbors."
                    ),
                    recommendation=(
                        f"Set a uniform MTU on all interfaces in OSPF area {area}, "
                        "or configure 'ip ospf mtu-ignore' as a workaround."
                    ),
                    evidence={
                        "ospf_area": area,
                        "interface_mtu": mtu,
                        "all_mtus_in_area": sorted(mtus),
                        "ospf_network": network,
                    },
                ))

        return problems

    def _matches(self, ip: str, network: str, wildcard: Optional[str]) -> bool:
        """True when *ip* falls within the OSPF network statement."""
        try:
            iface_ip = ipaddress.ip_address(ip)
            if wildcard:
                wc_int = int(ipaddress.ip_address(wildcard))
                prefix = bin((~wc_int) & 0xFFFFFFFF).count("1")
                net = ipaddress.ip_network(f"{network}/{prefix}", strict=False)
            else:
                net = ipaddress.ip_network(network, strict=False)
            return iface_ip in net
        except Exception:
            return network == ip


class BGPNeighborDownRule(BaseRule):
    """
    L3_BGP_001 — BGP neighbor configured with 'shutdown' — session is not
    established and the peer's routes are not received.
    """

    rule_id = "L3_BGP_001"
    title = "BGP neighbor administratively shut down"
    category = Category.L3
    severity = Severity.CRITICAL

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        for device in devices:
            for proc in device.bgp_processes:
                for neighbor in proc.neighbors:
                    if neighbor.shutdown:
                        problems.append(self._make_problem(
                            device_hostname=device.hostname,
                            title="BGP neighbor shut down",
                            description=(
                                f"BGP neighbor {neighbor.address} "
                                f"(AS {neighbor.remote_as}) is configured but "
                                "administratively shut down."
                            ),
                            impact=(
                                "No BGP session — routes from this peer are "
                                "not installed in the routing table."
                            ),
                            recommendation=(
                                f"Remove 'neighbor {neighbor.address} shutdown' "
                                "if the session should be active."
                            ),
                            cli_fix=(
                                f"router bgp {proc.local_as}\n"
                                f" no neighbor {neighbor.address} shutdown"
                            ),
                            cli_fix_vendor="cisco",
                            evidence={
                                "neighbor_ip": neighbor.address,
                                "remote_as": neighbor.remote_as,
                                "local_as": proc.local_as,
                                "description": neighbor.description,
                            },
                        ))

        return problems


class VRFRouteLeakingRule(BaseRule):
    """
    L3_BGP_002 — Two VRFs on the same device share route-targets such that
    routes leak between them.  Unintended leaking exposes private segments.
    """

    rule_id = "L3_BGP_002"
    title = "Potential VRF route leaking"
    category = Category.L3
    severity = Severity.HIGH

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        for device in devices:
            vrfs = device.vrfs
            for i, vrf_a in enumerate(vrfs):
                for vrf_b in vrfs[i + 1:]:
                    a_exp = set(vrf_a.rt_export)
                    b_imp = set(vrf_b.rt_import)
                    a_imp = set(vrf_a.rt_import)
                    b_exp = set(vrf_b.rt_export)

                    leak_a_to_b = a_exp & b_imp
                    leak_b_to_a = b_exp & a_imp

                    if leak_a_to_b:
                        problems.append(self._make_problem(
                            device_hostname=device.hostname,
                            title="VRF route leaking detected",
                            description=(
                                f"VRF '{vrf_a.name}' exports RT(s) "
                                f"{sorted(leak_a_to_b)} that VRF '{vrf_b.name}' "
                                "imports — routes will leak between VRFs."
                            ),
                            impact=(
                                "Private networks may become reachable from "
                                "unintended VRFs, causing security or routing issues."
                            ),
                            recommendation=(
                                "Verify that leaking between "
                                f"'{vrf_a.name}' → '{vrf_b.name}' is intentional "
                                "and apply route-maps to restrict leaked prefixes."
                            ),
                            evidence={
                                "exporting_vrf": vrf_a.name,
                                "importing_vrf": vrf_b.name,
                                "leaked_route_targets": sorted(leak_a_to_b),
                            },
                        ))

                    if leak_b_to_a:
                        problems.append(self._make_problem(
                            device_hostname=device.hostname,
                            title="VRF route leaking detected",
                            description=(
                                f"VRF '{vrf_b.name}' exports RT(s) "
                                f"{sorted(leak_b_to_a)} that VRF '{vrf_a.name}' "
                                "imports — routes will leak between VRFs."
                            ),
                            impact=(
                                "Private networks may become reachable from "
                                "unintended VRFs, causing security or routing issues."
                            ),
                            recommendation=(
                                "Verify that leaking between "
                                f"'{vrf_b.name}' → '{vrf_a.name}' is intentional."
                            ),
                            evidence={
                                "exporting_vrf": vrf_b.name,
                                "importing_vrf": vrf_a.name,
                                "leaked_route_targets": sorted(leak_b_to_a),
                            },
                        ))

        return problems


class AsymmetricRoutingRule(BaseRule):
    """
    L3_ROUTING_001 — Static route whose next-hop IP does not match any
    known interface across all devices.  Traffic may be dropped or take an
    unexpected asymmetric return path.
    """

    rule_id = "L3_ROUTING_001"
    title = "Static route with unreachable next-hop"
    category = Category.L3
    severity = Severity.MEDIUM

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        # Collect all known interface IPs
        known_ips: set[str] = set()
        for device in devices:
            for iface in device.interfaces:
                if iface.ip_address:
                    known_ips.add(iface.ip_address)

        for device in devices:
            for route in device.static_routes:
                if route.next_hop and route.next_hop not in known_ips:
                    dest = (
                        f"{route.network}/{route.prefix_length}"
                        if route.prefix_length is not None
                        else route.network
                    )
                    problems.append(self._make_problem(
                        device_hostname=device.hostname,
                        title="Static route next-hop not found on any device",
                        description=(
                            f"Static route to {dest} via next-hop "
                            f"{route.next_hop} — that IP is not present on any "
                            "known device interface."
                        ),
                        impact=(
                            "Traffic may be dropped or routed asymmetrically "
                            "if the next-hop is unreachable."
                        ),
                        recommendation=(
                            "Verify next-hop reachability. Check for typos or "
                            "missing device configurations."
                        ),
                        evidence={
                            "destination": dest,
                            "next_hop": route.next_hop,
                            "metric": route.metric,
                            "vrf": route.vrf,
                            "protocol": route.protocol.value,
                        },
                    ))

        return problems
