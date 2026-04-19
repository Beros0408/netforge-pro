"""
Configuration settings for the Rule Engine module.
"""
from pydantic import Field
from pydantic_settings import BaseSettings


class RuleEngineSettings(BaseSettings):
    rule_enabled_categories: list[str] = Field(
        default=["l2", "l3", "security"],
        description="Enabled rule categories"
    )
    rule_min_severity: str = Field(
        default="low",
        description="Minimum severity to report (low/medium/high/critical)"
    )
    rule_max_problems_per_device: int = Field(
        default=100,
        description="Maximum problems to report per device"
    )
    rule_timeout_seconds: float = Field(
        default=30.0,
        description="Timeout for rule execution in seconds"
    )
    stp_root_min_trunk_count: int = Field(
        default=3,
        description="Minimum trunk count to trigger STP root bridge check"
    )
    stp_core_keywords: list[str] = Field(
        default=["core", "spine", "root", "dist", "backbone", "agg", "distribution"],
        description="Hostnames containing these keywords are considered core/distribution devices"
    )
