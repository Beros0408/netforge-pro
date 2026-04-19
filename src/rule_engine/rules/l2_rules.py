"""
Layer 2 rules — VLAN, STP, LACP, port state checks.
"""
from __future__ import annotations

from typing import List

from ...parser_engine.models.device import Device
from ...parser_engine.models.interface import InterfaceStatus, SwitchportMode
from ..models.problem import Category, Problem, Severity
from .base_rule import BaseRule


class VLANMismatchRule(BaseRule):
    """
    L2_VLAN_001 — Trunk port allows VLANs not defined in device VLAN table.

    Flags trunk interfaces whose allowed VLAN list contains IDs that have
    no corresponding VLAN entry on the device.
    """

    rule_id = "L2_VLAN_001"
    title = "VLAN mismatch on trunk"
    category = Category.L2
    severity = Severity.HIGH

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        for device in devices:
            defined_vlans = {v.vlan_id for v in device.vlans}
            if not defined_vlans:
                continue

            for iface in device.interfaces:
                if iface.switchport_mode != SwitchportMode.TRUNK or not iface.trunk_vlans:
                    continue

                missing = set(iface.trunk_vlans) - defined_vlans
                if missing:
                    problems.append(self._make_problem(
                        device_hostname=device.hostname,
                        interface=iface.name,
                        title="Trunk port carries undefined VLANs",
                        description=(
                            f"Trunk {iface.name} allows VLANs {sorted(missing)} "
                            f"that are not defined in the device VLAN database."
                        ),
                        impact="Traffic on undefined VLANs may be silently dropped.",
                        recommendation=(
                            "Add missing VLANs to the device VLAN database "
                            "or remove them from the trunk allowed list."
                        ),
                        evidence={
                            "trunk_vlans": sorted(iface.trunk_vlans),
                            "defined_vlans": sorted(defined_vlans),
                            "missing_vlans": sorted(missing),
                        },
                    ))

        # Cross-device: trunks sharing a native VLAN should agree on allowed VLANs
        trunk_by_native: dict[int, list[tuple[str, str, list[int]]]] = {}
        for device in devices:
            for iface in device.interfaces:
                if (
                    iface.switchport_mode == SwitchportMode.TRUNK
                    and iface.native_vlan
                    and iface.trunk_vlans
                ):
                    trunk_by_native.setdefault(iface.native_vlan, []).append(
                        (device.hostname, iface.name, iface.trunk_vlans)
                    )

        for native_vlan, trunks in trunk_by_native.items():
            if len(trunks) < 2:
                continue
            vlan_sets = [frozenset(t[2]) for t in trunks]
            if len(set(vlan_sets)) > 1:
                for dev_hostname, iface_name, trunk_vlans in trunks:
                    problems.append(self._make_problem(
                        device_hostname=dev_hostname,
                        interface=iface_name,
                        title="Cross-device trunk VLAN mismatch",
                        description=(
                            f"Trunk ports with native VLAN {native_vlan} have "
                            "different allowed VLAN sets across devices."
                        ),
                        impact="VLANs missing on one side will lose connectivity.",
                        recommendation=(
                            "Ensure all connected trunk ports carry identical "
                            "allowed VLAN lists."
                        ),
                        evidence={
                            "native_vlan": native_vlan,
                            "local_trunk_vlans": sorted(trunk_vlans),
                            "all_trunks": [
                                (h, n, sorted(v)) for h, n, v in trunks
                            ],
                        },
                    ))

        return problems


class UnexpectedRootBridgeRule(BaseRule):
    """
    L2_STP_001 — Device with many active trunk ports but non-core hostname
    may be acting as an unintended STP root bridge.
    """

    rule_id = "L2_STP_001"
    title = "Potential unexpected STP root bridge"
    category = Category.L2
    severity = Severity.CRITICAL

    _CORE_KEYWORDS = frozenset(
        ["core", "spine", "root", "dist", "backbone", "agg", "distribution"]
    )
    _MIN_TRUNK_COUNT = 3

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        for device in devices:
            hostname_lower = device.hostname.lower()
            is_core = any(kw in hostname_lower for kw in self._CORE_KEYWORDS)
            if is_core:
                continue

            active_trunks = [
                i for i in device.interfaces
                if i.switchport_mode == SwitchportMode.TRUNK
                and i.status == InterfaceStatus.UP
            ]

            if len(active_trunks) >= self._MIN_TRUNK_COUNT:
                problems.append(self._make_problem(
                    device_hostname=device.hostname,
                    title="Unexpected STP root bridge candidate",
                    description=(
                        f"Device '{device.hostname}' has {len(active_trunks)} active "
                        "trunk ports but its name does not indicate a core/distribution role."
                    ),
                    impact=(
                        "If this device becomes STP root, traffic will follow "
                        "suboptimal paths through access-layer equipment."
                    ),
                    recommendation=(
                        "Set explicit bridge priority (e.g. 4096) on intended root, "
                        "or raise priority (e.g. 61440) on access devices."
                    ),
                    cli_fix="spanning-tree vlan 1-4094 priority 61440",
                    cli_fix_vendor="cisco",
                    evidence={
                        "active_trunk_count": len(active_trunks),
                        "trunk_interfaces": [i.name for i in active_trunks],
                    },
                ))

        return problems


class PotentialLoopRule(BaseRule):
    """
    L2_STP_002 — Multiple trunk ports with identical VLAN sets and no
    port-channel — redundancy without LAG can cause broadcast storms.
    """

    rule_id = "L2_STP_002"
    title = "Redundant trunk links without LAG"
    category = Category.L2
    severity = Severity.CRITICAL

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        for device in devices:
            # Only physical trunks without port-channel aggregation
            trunk_ifaces = [
                i for i in device.interfaces
                if i.switchport_mode == SwitchportMode.TRUNK
                and i.channel_group is None
                and i.trunk_vlans
            ]

            vlan_set_map: dict[frozenset, list[str]] = {}
            for iface in trunk_ifaces:
                key = frozenset(iface.trunk_vlans)
                vlan_set_map.setdefault(key, []).append(iface.name)

            for vlan_set, iface_names in vlan_set_map.items():
                if len(iface_names) >= 2:
                    problems.append(self._make_problem(
                        device_hostname=device.hostname,
                        title="Redundant trunk links without port-channel",
                        description=(
                            f"Interfaces {iface_names} carry identical VLAN sets "
                            "without a port-channel (LAG)."
                        ),
                        impact=(
                            "Parallel links without LACP rely solely on STP; "
                            "STP failure may cause a broadcast storm."
                        ),
                        recommendation=(
                            "Bundle redundant links into a port-channel (LACP) "
                            "or verify STP is correctly protecting these links."
                        ),
                        evidence={
                            "interfaces": iface_names,
                            "shared_vlans": sorted(vlan_set),
                        },
                    ))

        return problems


class LACPInconsistentRule(BaseRule):
    """
    L2_LACP_001 — Port-channel member interfaces with mismatched
    MTU, speed, or duplex will fail to bundle under LACP.
    """

    rule_id = "L2_LACP_001"
    title = "Inconsistent port-channel member configuration"
    category = Category.L2
    severity = Severity.HIGH

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        for device in devices:
            by_channel: dict[int, list] = {}
            for iface in device.interfaces:
                if iface.channel_group is not None:
                    by_channel.setdefault(iface.channel_group, []).append(iface)

            for group_id, members in by_channel.items():
                if len(members) < 2:
                    continue

                mtus = {i.mtu for i in members if i.mtu is not None}
                speeds = {i.speed for i in members if i.speed is not None}
                duplexes = {i.duplex for i in members if i.duplex is not None}

                if len(mtus) > 1 or len(speeds) > 1 or len(duplexes) > 1:
                    problems.append(self._make_problem(
                        device_hostname=device.hostname,
                        title=f"Port-channel {group_id} has inconsistent member config",
                        description=(
                            f"Port-channel {group_id} members have mismatched "
                            "MTU, speed, or duplex settings."
                        ),
                        impact="LACP will not bundle interfaces with mismatched parameters.",
                        recommendation=(
                            "Set identical MTU, speed, and duplex on all "
                            f"port-channel {group_id} member interfaces."
                        ),
                        evidence={
                            "channel_group": group_id,
                            "members": [i.name for i in members],
                            "mtus": sorted(m for m in mtus if m is not None),
                            "speeds": sorted(s for s in speeds if s is not None),
                            "duplexes": sorted(d for d in duplexes if d is not None),
                        },
                    ))

        return problems


class ErrDisabledPortRule(BaseRule):
    """
    L2_PORT_001 — Interface administratively enabled but operationally down.
    Covers err-disabled, physical link failure, and SFP issues.
    """

    rule_id = "L2_PORT_001"
    title = "Interface down while admin-enabled"
    category = Category.L2
    severity = Severity.HIGH

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        for device in devices:
            for iface in device.interfaces:
                if iface.admin_status and iface.status == InterfaceStatus.DOWN:
                    problems.append(self._make_problem(
                        device_hostname=device.hostname,
                        interface=iface.name,
                        title="Interface operationally down (possible err-disabled)",
                        description=(
                            f"Interface {iface.name} is administratively enabled "
                            "but operationally DOWN."
                        ),
                        impact="Devices or services connected to this port are unreachable.",
                        recommendation=(
                            "Check for err-disabled cause with 'show interface' or "
                            "'show err-disabled'. Issue 'shutdown / no shutdown' to recover."
                        ),
                        cli_fix=f"interface {iface.name}\n shutdown\n no shutdown",
                        cli_fix_vendor="cisco",
                        evidence={
                            "admin_status": iface.admin_status,
                            "operational_status": iface.status.value,
                            "description": iface.description,
                            "interface_type": iface.interface_type.value,
                        },
                    ))

        return problems
