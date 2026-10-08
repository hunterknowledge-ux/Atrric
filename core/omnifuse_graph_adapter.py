"""
core/omnifuse_graph_adapter.py
RDBMSGraphStore — adapter kgrdbms.Graph -> OmniFuse KnowledgeGraphStore protocol.
Tidak sentuh kgrdbms. Hanya wrap.
"""

from pathlib import Path
from typing import Optional

from omnifuse.knowledge import GraphEntity, GraphFact

# kgrdbms
from kgrdbms.graph import Graph, Node, Edge
from kgrdbms.graph import default_graph_path

import config


# ============================================================
# Conversion helpers — kgrdbms Node/Edge <-> OmniFuse models
# ============================================================

def _node_to_entity(n: Node) -> GraphEntity:
    """Node -> GraphEntity."""
    return GraphEntity(
        id=n.id,
        label=n.name or n.id,
        kind="instance",
        extensions={"labels": list(n.labels) if n.labels else []},
    )


def _edge_to_fact(e: Edge) -> GraphFact:
    """Edge -> GraphFact."""
    return GraphFact(
        id=e.id,
        subject_id=e.from_node,
        predicate=e.type,
        object_id=e.to_node,
        assertion="extracted",
        extensions={"properties": dict(e.properties) if e.properties else {}},
    )


# ============================================================
# Adapter
# ============================================================

class RDBMSGraphStore:
    """OmniFuse KnowledgeGraphStore protocol over kgrdbms.Graph."""

    def __init__(self, path: Optional[str] = None):
        db_path = path or getattr(config, "GRAPH_DB_PATH", None)
        if db_path is None:
            # default ke ~/pocket_vectordb/graph.db
            base = Path(getattr(config, "POCKET_VECTOR_DIR", Path.home() / "pocket_vectordb"))
            db_path = str(base.parent / "graph.db")
        self._path = db_path
        self._graph = Graph(path=db_path)

    # --- optional lifecycle ---

    def close(self) -> None:
        try:
            self._graph.close()
        except Exception:
            pass

    # --- KnowledgeGraphStore protocol ---

    def search_entities(self, query: str, *, limit: int = 10) -> list[tuple[GraphEntity, float]]:
        q = (query or "").strip().lower()
        if not q:
            return []
        out: list[tuple[GraphEntity, float]] = []
        for n in self._all_nodes():
            name = (n.name or "").lower()
            if q in name:
                # score ringkas: panjang match ratio
                score = len(q) / max(len(name), 1)
                out.append((_node_to_entity(n), score))
        out.sort(key=lambda x: x[1], reverse=True)
        return out[:limit]

    def get_entities(self, ids: list[str]) -> list[GraphEntity]:
        out = []
        for i in ids:
            n = self._graph.node(i)
            if n is not None:
                out.append(_node_to_entity(n))
        return out

    def get_entity(self, entity_id: str) -> Optional[GraphEntity]:
        n = self._graph.node(entity_id)
        return _node_to_entity(n) if n is not None else None

    def neighbors(
        self,
        entity_id: str,
        *,
        direction: str = "both",
        limit: int = 100,
    ) -> list[GraphFact]:
        edges = self._graph.neighbors(entity_id, direction=direction)
        if limit and len(edges) > limit:
            edges = edges[:limit]
        return [_edge_to_fact(e) for e in edges]

    def get_facts(self, entity_id: str, *, limit: int = 100) -> list[GraphFact]:
        # POC: same as neighbors, no cursor pagination
        return self.neighbors(entity_id, direction="both", limit=limit)

    # --- stubs (kgrdbms tak track entity<->chunk link) ---

    def entities_for_chunk(self, chunk_ids: list[str]) -> list[tuple[GraphEntity, float]]:
        return []

    def entity_chunk_counts(self, entity_ids: list[str]) -> dict[str, int]:
        return {}

    def chunks_for_entities(self, entity_ids: list[str], *, limit: int = 1000) -> list[str]:
        return []

    # --- internal ---

    def _all_nodes(self) -> list[Node]:
        """Best-effort: cuba beberapa API, fallback ke SQLite direct."""
        g = self._graph
        for meth in ("all_nodes", "nodes", "iter_nodes"):
            fn = getattr(g, meth, None)
            if callable(fn):
                try:
                    return list(fn())
                except Exception:
                    pass
        # fallback: SQLite direct
        try:
            conn = getattr(g, "_conn", None) or getattr(g, "conn", None)
            if conn is not None:
                rows = conn.execute("SELECT id, kind, name FROM nodes").fetchall()
                return [Node(id=r[0], kind=r[1], name=r[2]) for r in rows]
        except Exception:
            pass
        return []