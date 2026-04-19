"""
Graph database API endpoints.
"""
from .routes import router, init_graph_api

__all__ = [
    "router",
    "init_graph_api",
]