"""
Neo4j service for graph database operations.
Provides async connection management and basic CRUD operations.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import ClientError, DatabaseError, ServiceUnavailable

from ..config import GraphSettings

logger = logging.getLogger(__name__)


class Neo4jService:
    """
    Async Neo4j service for graph database operations.

    Provides connection management, transaction handling, and basic CRUD operations.
    """

    def __init__(self, settings: GraphSettings):
        """
        Initialize Neo4j service with configuration.

        Args:
            settings: Graph database configuration
        """
        self.settings = settings
        self._driver = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """
        Establish connection to Neo4j database.

        Raises:
            ServiceUnavailable: If connection cannot be established
        """
        async with self._lock:
            if self._driver is not None:
                return

            try:
                self._driver = AsyncGraphDatabase.driver(
                    self.settings.neo4j_uri,
                    auth=self.settings.neo4j_auth,
                    max_connection_pool_size=self.settings.neo4j_max_connection_pool_size,
                    connection_timeout=self.settings.neo4j_connection_timeout,
                    max_connection_lifetime=self.settings.neo4j_max_connection_lifetime,
                )

                # Test connection
                await self._driver.verify_connectivity()
                logger.info(f"Connected to Neo4j at {self.settings.neo4j_uri}")

            except ServiceUnavailable as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error connecting to Neo4j: {e}")
                raise ServiceUnavailable(f"Neo4j connection failed: {e}")

    async def disconnect(self) -> None:
        """
        Close Neo4j database connection.
        """
        async with self._lock:
            if self._driver is not None:
                await self._driver.close()
                self._driver = None
                logger.info("Disconnected from Neo4j")

    async def is_connected(self) -> bool:
        """
        Check if Neo4j connection is active.

        Returns:
            True if connected, False otherwise
        """
        if self._driver is None:
            return False

        try:
            await self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for Neo4j session.

        Yields:
            AsyncSession: Neo4j session for database operations
        """
        if self._driver is None:
            await self.connect()

        session = self._driver.session(database=self.settings.neo4j_database)
        try:
            yield session
        finally:
            await session.close()

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        read_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters
            read_only: If True, use read transaction

        Returns:
            List of result records as dictionaries

        Raises:
            DatabaseError: If query execution fails
        """
        parameters = parameters or {}

        async with self.session() as session:
            try:
                if read_only:
                    result = await session.execute_read(
                        lambda tx: tx.run(query, parameters).data()
                    )
                else:
                    result = await session.execute_write(
                        lambda tx: tx.run(query, parameters).data()
                    )
                return result

            except ClientError as e:
                logger.error(f"Cypher syntax error in query: {query}")
                raise DatabaseError(f"Cypher error: {e}")
            except Exception as e:
                logger.error(f"Query execution failed: {query}")
                raise DatabaseError(f"Query failed: {e}")

    async def create_node(
        self,
        labels: List[str],
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new node in the graph.

        Args:
            labels: Node labels
            properties: Node properties

        Returns:
            Created node data
        """
        label_string = ":".join(labels)
        prop_keys = list(properties.keys())
        prop_placeholders = [f"{key}: ${key}" for key in prop_keys]

        query = f"""
        CREATE (n:{label_string} {{
            {', '.join(prop_placeholders)},
            created_at: datetime(),
            updated_at: datetime()
        }})
        RETURN n
        """

        result = await self.execute_query(query, properties)
        return result[0]["n"] if result else {}

    async def create_relationship(
        self,
        start_node_id: int,
        end_node_id: int,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between two nodes.

        Args:
            start_node_id: Starting node ID
            end_node_id: Ending node ID
            relationship_type: Relationship type
            properties: Relationship properties

        Returns:
            Created relationship data
        """
        properties = properties or {}
        prop_keys = list(properties.keys())
        prop_placeholders = [f"{key}: ${key}" for key in prop_keys]

        props_string = f" {{ {', '.join(prop_placeholders)} }}" if prop_keys else ""

        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $start_id AND id(b) = $end_id
        CREATE (a)-[r:{relationship_type}{props_string} {{
            created_at: datetime(),
            updated_at: datetime()
        }}]->(b)
        RETURN r
        """

        params = {
            "start_id": start_node_id,
            "end_id": end_node_id,
            **properties
        }

        result = await self.execute_query(query, params)
        return result[0]["r"] if result else {}

    async def find_node(
        self,
        labels: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single node by labels and properties.

        Args:
            labels: Node labels to match
            properties: Properties to match

        Returns:
            Node data if found, None otherwise
        """
        labels = labels or []
        properties = properties or {}

        label_filter = ""
        if labels:
            label_string = ":".join(labels)
            label_filter = f":{label_string}"

        where_clauses = []
        params = {}

        for key, value in properties.items():
            where_clauses.append(f"n.{key} = ${key}")
            params[key] = value

        where_string = ""
        if where_clauses:
            where_string = f"WHERE {' AND '.join(where_clauses)}"

        query = f"""
        MATCH (n{label_filter})
        {where_string}
        RETURN n
        LIMIT 1
        """

        result = await self.execute_query(query, params, read_only=True)
        return result[0]["n"] if result else None

    async def find_nodes(
        self,
        labels: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple nodes by labels and properties.

        Args:
            labels: Node labels to match
            properties: Properties to match
            limit: Maximum number of results

        Returns:
            List of matching nodes
        """
        labels = labels or []
        properties = properties or {}

        label_filter = ""
        if labels:
            label_string = ":".join(labels)
            label_filter = f":{label_string}"

        where_clauses = []
        params = {}

        for key, value in properties.items():
            where_clauses.append(f"n.{key} = ${key}")
            params[key] = value

        where_string = ""
        if where_clauses:
            where_string = f"WHERE {' AND '.join(where_clauses)}"

        limit_string = f"LIMIT {limit}" if limit else ""

        query = f"""
        MATCH (n{label_filter})
        {where_string}
        RETURN n
        {limit_string}
        """

        result = await self.execute_query(query, params, read_only=True)
        return [record["n"] for record in result]

    async def delete_node(self, node_id: int) -> bool:
        """
        Delete a node and all its relationships.

        Args:
            node_id: Node ID to delete

        Returns:
            True if node was deleted, False if not found
        """
        query = """
        MATCH (n)
        WHERE id(n) = $node_id
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """

        result = await self.execute_query(query, {"node_id": node_id})
        return result[0]["deleted_count"] > 0 if result else False

    async def clear_database(self) -> None:
        """
        Clear all nodes and relationships from the database.
        USE WITH CAUTION - This will delete all data!
        """
        query = "MATCH (n) DETACH DELETE n"
        await self.execute_query(query)
        logger.warning("Database cleared - all data deleted")

    async def get_database_stats(self) -> Dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with node and relationship counts
        """
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->()
        RETURN
            count(DISTINCT n) as node_count,
            count(DISTINCT r) as relationship_count
        """

        result = await self.execute_query(query, read_only=True)
        if result:
            return {
                "node_count": result[0]["node_count"],
                "relationship_count": result[0]["relationship_count"]
            }
        return {"node_count": 0, "relationship_count": 0}