"""
Configuration settings for the Discovery Engine module.
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class DiscoverySettings(BaseSettings):
    """
    Discovery Engine configuration loaded from environment variables.
    """

    # Module metadata
    module_name: str = Field(default="NetForge Discovery Engine", description="Module name")
    module_version: str = Field(default="1.0.0", description="Module version")
    debug: bool = Field(default=False, description="Enable debug logging")

    # Network scanning
    scan_timeout_seconds: int = Field(
        default=5, description="Timeout for individual host scans"
    )
    max_concurrent_scans: int = Field(
        default=50, description="Maximum concurrent network scans"
    )
    scan_rate_limit: int = Field(
        default=1000, description="Maximum scans per minute"
    )

    # Port scanning
    default_ports: List[int] = Field(
        default=[22, 23, 161, 443], description="Default ports to scan"
    )
    port_scan_timeout: float = Field(
        default=1.0, description="Timeout for port scans in seconds"
    )

    # SNMP settings
    snmp_timeout: float = Field(
        default=2.0, description="SNMP timeout in seconds"
    )
    snmp_retries: int = Field(
        default=2, description="Number of SNMP retries"
    )
    snmp_community_strings: List[str] = Field(
        default=["public", "private"], description="SNMP community strings to try"
    )

    # SSH settings
    ssh_timeout: float = Field(
        default=5.0, description="SSH connection timeout in seconds"
    )
    ssh_banner_timeout: float = Field(
        default=2.0, description="SSH banner read timeout in seconds"
    )

    # Auto-discovery
    max_discovery_hops: int = Field(
        default=3, description="Maximum hops for auto-discovery"
    )
    discovery_batch_size: int = Field(
        default=10, description="Batch size for parallel discovery"
    )

    # Fingerprinting weights
    snmp_fingerprint_weight: float = Field(
        default=0.5, description="Weight for SNMP fingerprinting (50%)"
    )
    ssh_fingerprint_weight: float = Field(
        default=0.3, description="Weight for SSH fingerprinting (30%)"
    )
    mac_fingerprint_weight: float = Field(
        default=0.2, description="Weight for MAC OUI fingerprinting (20%)"
    )

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable discovery caching")
    cache_ttl_seconds: int = Field(
        default=1800, description="Cache time-to-live in seconds (30 minutes)"
    )

    # Supported vendors for fingerprinting
    supported_vendors: List[str] = Field(
        default=[
            "cisco",
            "huawei",
            "arista",
            "fortinet",
            "juniper",
            "extreme",
            "brocade",
            "hp",
            "dell",
            "unknown"
        ],
        description="Supported network vendors"
    )


# Global settings instance
settings = DiscoverySettings()