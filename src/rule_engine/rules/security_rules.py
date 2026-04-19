"""
Security rules — ACL, firewall policy checks.
"""
from __future__ import annotations

from typing import List

from ...parser_engine.models.device import Device
from ...parser_engine.models.security import ACLAction, FirewallPolicyAction
from ..models.problem import Category, Problem, Severity
from .base_rule import BaseRule


_ANY_KEYWORDS = frozenset(["all", "any", "0.0.0.0/0", "0.0.0.0 255.255.255.255"])
_CATCH_ALL_SOURCES = frozenset(["any", "0.0.0.0 255.255.255.255", None])
_CATCH_ALL_PROTOS = frozenset(["ip", "any", None])


class ShadowedACLRule(BaseRule):
    """
    SEC_ACL_001 — ACL entry that follows a catch-all (permit/deny any)
    rule and will therefore never be evaluated.
    """

    rule_id = "SEC_ACL_001"
    title = "Shadowed ACL entry"
    category = Category.SECURITY
    severity = Severity.MEDIUM

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        for device in devices:
            for acl in device.acls:
                shadow_entry = None

                for entry in acl.entries:
                    if entry.remark:
                        continue

                    if shadow_entry is not None:
                        problems.append(self._make_problem(
                            device_hostname=device.hostname,
                            title="Unreachable ACL entry (shadowed)",
                            description=(
                                f"ACL '{acl.name}': entry seq {entry.sequence} "
                                f"({entry.action.value}) is unreachable because "
                                f"catch-all entry seq {shadow_entry.sequence} "
                                f"({shadow_entry.action.value} any) precedes it."
                            ),
                            impact=(
                                "This ACL entry is never evaluated — "
                                "its intent (permit/deny) has no effect."
                            ),
                            recommendation=(
                                "Remove the shadowed entry or reorder ACL entries "
                                "so specific rules appear before catch-all rules."
                            ),
                            evidence={
                                "acl_name": acl.name,
                                "shadowed_seq": entry.sequence,
                                "shadowed_action": entry.action.value,
                                "shadow_cause_seq": shadow_entry.sequence,
                                "shadow_cause_action": shadow_entry.action.value,
                            },
                        ))
                        continue

                    # Detect catch-all entry
                    src_any = entry.source in _CATCH_ALL_SOURCES
                    dst_any = entry.destination in _CATCH_ALL_SOURCES
                    proto_any = entry.protocol in _CATCH_ALL_PROTOS
                    if src_any and dst_any and proto_any:
                        shadow_entry = entry

        return problems


class AnyAnyPermitRule(BaseRule):
    """
    SEC_FW_001 — Active firewall policy that permits all traffic from any
    source to any destination (any-any permit).
    """

    rule_id = "SEC_FW_001"
    title = "Firewall any-any permit rule"
    category = Category.SECURITY
    severity = Severity.CRITICAL

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []

        for device in devices:
            for policy in device.firewall_policies:
                if not policy.status:
                    continue

                src_any = not policy.source_addresses or all(
                    s.lower() in _ANY_KEYWORDS for s in policy.source_addresses
                )
                dst_any = not policy.destination_addresses or all(
                    d.lower() in _ANY_KEYWORDS for d in policy.destination_addresses
                )
                is_permit = policy.action == FirewallPolicyAction.ACCEPT

                if src_any and dst_any and is_permit:
                    problems.append(self._make_problem(
                        device_hostname=device.hostname,
                        title="Any-any firewall permit detected",
                        description=(
                            f"Firewall policy {policy.policy_id} "
                            f"('{policy.name or 'unnamed'}') permits ALL traffic "
                            "from any source to any destination."
                        ),
                        impact=(
                            "Firewall offers no protection — all traffic is "
                            "allowed regardless of source, destination, or service."
                        ),
                        recommendation=(
                            "Replace with explicit permit rules matching "
                            "specific source/destination/service combinations. "
                            "Add a default-deny rule at the end."
                        ),
                        evidence={
                            "policy_id": policy.policy_id,
                            "policy_name": policy.name,
                            "source_addresses": policy.source_addresses,
                            "destination_addresses": policy.destination_addresses,
                            "action": policy.action.value,
                        },
                    ))

        return problems


class ContradictoryACLRule(BaseRule):
    """
    SEC_ACL_002 — Two ACL entries matching the same traffic flow but with
    opposite actions (one permit, one deny).  The later entry is shadowed
    and its intent is silently ignored.
    """

    rule_id = "SEC_ACL_002"
    title = "Contradictory ACL entries"
    category = Category.SECURITY
    severity = Severity.HIGH

    def check(self, devices: List[Device]) -> List[Problem]:
        problems: List[Problem] = []
        seen: set[tuple] = set()

        for device in devices:
            for acl in device.acls:
                real_entries = [
                    e for e in acl.entries
                    if not e.remark and e.sequence is not None
                ]

                for i, entry_a in enumerate(real_entries):
                    for entry_b in real_entries[i + 1:]:
                        same_flow = (
                            entry_a.protocol == entry_b.protocol
                            and entry_a.source == entry_b.source
                            and entry_a.destination == entry_b.destination
                        )
                        contradicts = entry_a.action != entry_b.action

                        if not (same_flow and contradicts):
                            continue

                        dedup_key = (
                            device.hostname, acl.name,
                            entry_a.sequence, entry_b.sequence,
                        )
                        if dedup_key in seen:
                            continue
                        seen.add(dedup_key)

                        problems.append(self._make_problem(
                            device_hostname=device.hostname,
                            title="Contradictory ACL entries for same flow",
                            description=(
                                f"ACL '{acl.name}': seq {entry_a.sequence} "
                                f"({entry_a.action.value}) and seq {entry_b.sequence} "
                                f"({entry_b.action.value}) match identical traffic "
                                f"(proto={entry_a.protocol}, "
                                f"src={entry_a.source}, dst={entry_a.destination})."
                            ),
                            impact=(
                                f"Entry seq {entry_b.sequence} "
                                f"({entry_b.action.value}) is shadowed by "
                                f"seq {entry_a.sequence} and never evaluated."
                            ),
                            recommendation=(
                                "Review the intent of both entries and remove "
                                "the redundant or incorrect one."
                            ),
                            evidence={
                                "acl_name": acl.name,
                                "first_seq": entry_a.sequence,
                                "first_action": entry_a.action.value,
                                "second_seq": entry_b.sequence,
                                "second_action": entry_b.action.value,
                                "protocol": entry_a.protocol,
                                "source": entry_a.source,
                                "destination": entry_a.destination,
                            },
                        ))

        return problems
