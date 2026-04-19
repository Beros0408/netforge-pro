"""
Problem model — represents a detected configuration issue.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(str, Enum):
    L2 = "l2"
    L3 = "l3"
    SECURITY = "security"


class Problem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    rule_id: str = Field(..., description="Rule identifier (e.g. L2_VLAN_001)")
    category: Category
    severity: Severity
    device_hostname: str
    interface: Optional[str] = None
    title: str
    description: str
    impact: str
    recommendation: str
    cli_fix: Optional[str] = None
    cli_fix_vendor: Optional[str] = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self) -> str:
        loc = f" [{self.interface}]" if self.interface else ""
        return f"[{self.severity.value.upper()}] {self.rule_id} @ {self.device_hostname}{loc}: {self.title}"
