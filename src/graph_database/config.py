"""
Configuration settings for the Graph Database module.
"""
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class GraphSettings(BaseSettings):
    """
    Neo4j graph database settings loaded from environment variables.
    """

    # Neo4j connection settings
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI"
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: str = Field(
        default="password",
        description="Neo4j password"
    )
    neo4j_database: str = Field(
        default="neo4j",
        description="Neo4j database name"
    )

    # Connection pool settings
    neo4j_max_connection_pool_size: int = Field(
        default=50,
        description="Maximum connection pool size"
    )
    neo4j_connection_timeout: float = Field(
        default=30.0,
        description="Connection timeout in seconds"
    )
    neo4j_max_connection_lifetime: float = Field(
        default=3600.0,
        description="Maximum connection lifetime in seconds"
    )

    # Graph building settings
    graph_batch_size: int = Field(
        default=100,
        description="Batch size for bulk graph operations"
    )
    graph_build_timeout: float = Field(
        default=300.0,
        description="Timeout for graph building operations"
    )

    # Query settings
    graph_query_timeout: float = Field(
        default=60.0,
        description="Timeout for graph queries in seconds"
    )
    graph_max_path_length: int = Field(
        default=10,
        description="Maximum path length for pathfinding queries"
    )

    @computed_field
    @property
    def neo4j_auth(self) -> tuple[str, str]:
        """Neo4j authentication tuple."""
        return (self.neo4j_user, self.neo4j_password)