from collections.abc import Callable

from ...graph_runtime_backend import ApiGraphRuntimeBackend
from .expand_neighbors import build_expand_neighbors_tool
from .lookup_nodes import build_lookup_nodes_tool
from .read_cypher import build_read_cypher_tool
from .search_edges import build_search_edges_tool
from .search_nodes import build_search_nodes_tool


def build_graph_tools(
    backend_factory: Callable[[], ApiGraphRuntimeBackend] | None = None,
):
    return [
        build_search_nodes_tool(backend_factory=backend_factory),
        build_search_edges_tool(backend_factory=backend_factory),
        build_expand_neighbors_tool(backend_factory=backend_factory),
        build_lookup_nodes_tool(backend_factory=backend_factory),
        build_read_cypher_tool(backend_factory=backend_factory),
    ]
