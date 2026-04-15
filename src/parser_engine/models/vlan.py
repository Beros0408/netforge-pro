"""
VLAN model — represents a single VLAN entry parsed from device configuration.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VLANStatus(str, Enum):
    """Administrative status of a VLAN."""

    ACTIVE = "active"
    SUSPEND = "suspend"
    UNKNOWN = "unknown"


class VLAN(BaseModel):
    """
    Represents a VLAN definition parsed from device configuration.

    Attributes:
        vlan_id: Numeric VLAN identifier (1-4094).
        name: Operator-assigned VLAN name.
        status: Administrative status (active / suspend).
        interfaces: Names of interfaces assigned to this VLAN.
        description: Optional free-form description.
    """

    vlan_id: int = Field(..., ge=1, le=4094, description="VLAN identifier")
    name: Optional[str] = Field(None, description="VLAN name")
    status: VLANStatus = Field(default=VLANStatus.ACTIVE, description="Administrative status")
    interfaces: list[str] = Field(
        default_factory=list, description="Interface names assigned to this VLAN"
    )
    description: Optional[str] = Field(None, description="VLAN description")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        """Strip surrounding whitespace from the VLAN name."""
        return v.strip() if v else v

    def __str__(self) -> str:
        name_part = f" ({self.name})" if self.name else ""
        return f"VLAN{self.vlan_id}{name_part} [{self.status.value}]"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VLAN):
            return self.vlan_id == other.vlan_id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.vlan_id)


def parse_vlan_range(vlan_range: str) -> list[int]:
    """
    Expand a Cisco-style VLAN range string to a list of VLAN IDs.

    Examples:
        "1-10"         → [1, 2, 3, ..., 10]
        "10,20,30-32"  → [10, 20, 30, 31, 32]
        "all"          → [1..4094]
        "none"         → []

    Args:
        vlan_range: VLAN range string from configuration.

    Returns:
        Sorted list of unique VLAN IDs.

    Raises:
        ValueError: If the range string cannot be parsed.
    """
    vlan_range = vlan_range.strip().lower()
    if vlan_range in ("none", ""):
        return []
    if vlan_range == "all":
        return list(range(1, 4095))

    result: list[int] = []
    for part in vlan_range.split(","):
        part = part.strip()
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start, end = int(start_str), int(end_str)
            if start > end or start < 1 or end > 4094:
                raise ValueError(f"Invalid VLAN range: {part}")
            result.extend(range(start, end + 1))
        else:
            vlan_id = int(part)
            if vlan_id < 1 or vlan_id > 4094:
                raise ValueError(f"VLAN ID out of range: {vlan_id}")
            result.append(vlan_id)

    return sorted(set(result))
