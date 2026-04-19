"""
Base rule — abstract class all rules must inherit from.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ...parser_engine.models.device import Device
from ..models.problem import Category, Problem, Severity


class BaseRule(ABC):
    """
    Abstract base class for all network configuration rules.

    Subclasses define rule_id, title, category, severity and implement check().
    """

    rule_id: str = ""
    title: str = ""
    category: Category = Category.L2
    severity: Severity = Severity.MEDIUM

    @abstractmethod
    def check(self, devices: List[Device]) -> List[Problem]:
        """
        Analyse a list of devices and return detected problems.

        Args:
            devices: Parsed device configurations to analyse.

        Returns:
            List of Problem instances (empty if no issues found).
        """
        ...

    def _make_problem(
        self,
        device_hostname: str,
        title: str,
        description: str,
        impact: str,
        recommendation: str,
        interface: Optional[str] = None,
        cli_fix: Optional[str] = None,
        cli_fix_vendor: Optional[str] = None,
        evidence: Optional[dict] = None,
        severity: Optional[Severity] = None,
    ) -> Problem:
        """Helper to build a Problem with rule metadata pre-filled."""
        return Problem(
            rule_id=self.rule_id,
            category=self.category,
            severity=severity or self.severity,
            device_hostname=device_hostname,
            interface=interface,
            title=title,
            description=description,
            impact=impact,
            recommendation=recommendation,
            cli_fix=cli_fix,
            cli_fix_vendor=cli_fix_vendor,
            evidence=evidence or {},
        )
