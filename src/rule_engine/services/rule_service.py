"""
Rule service — orchestrates all rules and exposes a clean analysis API.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ...parser_engine.models.device import Device
from ..config import RuleEngineSettings
from ..models.problem import Category, Problem, Severity
from ..rules.base_rule import BaseRule
from ..rules.l2_rules import (
    ErrDisabledPortRule,
    LACPInconsistentRule,
    PotentialLoopRule,
    UnexpectedRootBridgeRule,
    VLANMismatchRule,
)
from ..rules.l3_rules import (
    AsymmetricRoutingRule,
    BGPNeighborDownRule,
    OSPFAreaMismatchRule,
    OSPFMTUMismatchRule,
    VRFRouteLeakingRule,
)
from ..rules.security_rules import (
    AnyAnyPermitRule,
    ContradictoryACLRule,
    ShadowedACLRule,
)

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}


class RuleService:
    """
    Orchestrates rule execution against a list of parsed devices.

    Provides methods to run all rules, filter by category or severity,
    and query rule metadata.
    """

    def __init__(self, settings: Optional[RuleEngineSettings] = None):
        self.settings = settings or RuleEngineSettings()
        self._rules: List[BaseRule] = self._load_rules()

    def _load_rules(self) -> List[BaseRule]:
        return [
            # L2
            VLANMismatchRule(),
            UnexpectedRootBridgeRule(),
            PotentialLoopRule(),
            LACPInconsistentRule(),
            ErrDisabledPortRule(),
            # L3
            OSPFAreaMismatchRule(),
            OSPFMTUMismatchRule(),
            BGPNeighborDownRule(),
            VRFRouteLeakingRule(),
            AsymmetricRoutingRule(),
            # Security
            ShadowedACLRule(),
            AnyAnyPermitRule(),
            ContradictoryACLRule(),
        ]

    # ------------------------------------------------------------------
    # Core analysis methods
    # ------------------------------------------------------------------

    def analyse(self, devices: List[Device]) -> List[Problem]:
        """
        Run all enabled rules against *devices* and return every detected problem.

        Problems are sorted by severity (CRITICAL first) then by rule_id.
        """
        all_problems: List[Problem] = []
        enabled = set(self.settings.rule_enabled_categories)

        for rule in self._rules:
            if rule.category.value not in enabled:
                continue
            try:
                problems = rule.check(devices)
                all_problems.extend(problems)
            except Exception as exc:
                logger.error("Rule %s failed: %s", rule.rule_id, exc)

        return self._sort_and_filter(all_problems)

    def analyse_by_category(
        self, devices: List[Device], category: Category
    ) -> List[Problem]:
        """Run only rules belonging to *category*."""
        problems: List[Problem] = []
        for rule in self._rules:
            if rule.category != category:
                continue
            try:
                problems.extend(rule.check(devices))
            except Exception as exc:
                logger.error("Rule %s failed: %s", rule.rule_id, exc)
        return self._sort_and_filter(problems)

    def analyse_by_rule(self, devices: List[Device], rule_id: str) -> List[Problem]:
        """Run a single rule identified by *rule_id*."""
        for rule in self._rules:
            if rule.rule_id == rule_id:
                try:
                    return rule.check(devices)
                except Exception as exc:
                    logger.error("Rule %s failed: %s", rule.rule_id, exc)
                    return []
        raise ValueError(f"Unknown rule_id: {rule_id!r}")

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def list_rules(self) -> List[Dict]:
        """Return metadata for all registered rules."""
        return [
            {
                "rule_id": r.rule_id,
                "title": r.title,
                "category": r.category.value,
                "severity": r.severity.value,
            }
            for r in self._rules
        ]

    def get_rule_info(self, rule_id: str) -> Optional[Dict]:
        """Return metadata for a single rule, or None if not found."""
        for rule in self._rules:
            if rule.rule_id == rule_id:
                return {
                    "rule_id": rule.rule_id,
                    "title": rule.title,
                    "category": rule.category.value,
                    "severity": rule.severity.value,
                }
        return None

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------

    def summarise(self, problems: List[Problem]) -> Dict:
        """Return a count summary broken down by severity and category."""
        by_severity: Dict[str, int] = {s.value: 0 for s in Severity}
        by_category: Dict[str, int] = {c.value: 0 for c in Category}
        by_rule: Dict[str, int] = {}

        for p in problems:
            by_severity[p.severity.value] += 1
            by_category[p.category.value] += 1
            by_rule[p.rule_id] = by_rule.get(p.rule_id, 0) + 1

        return {
            "total": len(problems),
            "by_severity": by_severity,
            "by_category": by_category,
            "by_rule": by_rule,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sort_and_filter(self, problems: List[Problem]) -> List[Problem]:
        min_order = _SEVERITY_ORDER.get(
            Severity(self.settings.rule_min_severity), 0
        )
        filtered = [
            p for p in problems
            if _SEVERITY_ORDER.get(p.severity, 0) >= min_order
        ]
        return sorted(
            filtered,
            key=lambda p: (-_SEVERITY_ORDER.get(p.severity, 0), p.rule_id),
        )
