"""
Configuration settings for the Parser Engine module.
"""
from pydantic import Field
from pydantic_settings import BaseSettings


class ParserSettings(BaseSettings):
    """
    Parser Engine configuration loaded from environment variables.
    """

    # Module metadata
    module_name: str = Field(default="NetForge Parser Engine", description="Module name")
    module_version: str = Field(default="1.0.0", description="Module version")
    debug: bool = Field(default=False, description="Enable debug logging")

    # Parser behaviour
    max_config_size_mb: int = Field(
        default=10, description="Maximum configuration file size in MB"
    )
    parser_timeout_seconds: int = Field(
        default=30, description="Parsing timeout in seconds"
    )
    strict_mode: bool = Field(
        default=False,
        description="Raise errors on unrecognised config stanzas instead of skipping",
    )

    # Cache (Redis)
    cache_enabled: bool = Field(default=True, description="Enable parsed-result caching")
    cache_ttl_seconds: int = Field(
        default=3600, description="Cache time-to-live in seconds"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/1",
        description="Redis URL (separate DB from api_backend)",
    )

    # Supported vendors
    supported_vendors: list[str] = Field(
        default=[
            "cisco_ios",
            "cisco_nxos",
            "cisco_iosxe",
            "cisco_iosxr",
            "fortinet_fortios",
            "huawei_vrp",
            "arista_eos",
        ],
        description="List of supported vendor OS identifiers",
    )

    model_config = {
        "env_file": ".env",
        "env_prefix": "PARSER_",
        "case_sensitive": False,
    }


# Global settings instance
settings = ParserSettings()
