"""Runtime access to the generated, read-only Ao resource reference graph."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


REFERENCE_GRAPH_SCHEMA_VERSION = 1
UI_LOCALE_MAP = {"zh_cn": "zh_cle", "ja": "ja", "en": "en"}


def _locale(locale):
    return UI_LOCALE_MAP.get(str(locale or "zh_cn"), "zh_cle")


@dataclass(frozen=True)
class ReferenceNode:
    data: dict

    @property
    def id(self):
        return self.data["id"]

    @property
    def kind(self):
        return self.data["kind"]

    @property
    def issue(self):
        return bool(self.data.get("issue"))

    def label(self, locale="zh_cn"):
        labels = self.data.get("labels", {})
        language = _locale(locale)
        return labels.get(language) or labels.get("en") or labels.get("ja") or self.id


@dataclass(frozen=True)
class ReferenceEdge:
    data: dict

    @property
    def source(self):
        return self.data["source"]

    @property
    def target(self):
        return self.data["target"]

    @property
    def relation(self):
        return self.data["relation"]

    @property
    def confidence(self):
        return self.data["confidence"]


@dataclass(frozen=True)
class ReferenceLink:
    edge: ReferenceEdge
    node: ReferenceNode
    direction: str


@dataclass(frozen=True)
class ReferenceExplanation:
    node: ReferenceNode
    links: tuple


class ReferenceGraph:
    """Deep module owning graph validation, localization, search, and traversal."""

    def __init__(self, nodes=(), edges=(), metadata=None):
        self._nodes = tuple(nodes)
        self._by_id = {}
        for node in self._nodes:
            if not isinstance(node, ReferenceNode):
                raise TypeError("nodes must contain ReferenceNode values")
            if node.id in self._by_id:
                raise ValueError(f"duplicate reference node: {node.id}")
            self._by_id[node.id] = node

        self._edges = tuple(edges)
        self._links = {node.id: [] for node in self._nodes}
        for edge in self._edges:
            if not isinstance(edge, ReferenceEdge):
                raise TypeError("edges must contain ReferenceEdge values")
            if edge.source not in self._by_id or edge.target not in self._by_id:
                raise ValueError(
                    f"reference edge has missing endpoint: {edge.source} -> {edge.target}"
                )
            self._links[edge.source].append((edge, edge.target, "outbound"))
            self._links[edge.target].append((edge, edge.source, "inbound"))
        self.metadata = dict(metadata or {})
        self._search_text = {
            node.id: self._make_search_text(node.data) for node in self._nodes
        }

    @staticmethod
    def _make_search_text(data):
        values = []

        def collect(value):
            if isinstance(value, dict):
                for child in value.values():
                    collect(child)
            elif isinstance(value, (list, tuple)):
                for child in value:
                    collect(child)
            elif value is not None:
                values.append(str(value))

        collect(data)
        return " ".join(values).casefold()

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("reference graph root must be an object")
        if data.get("schema_version") != REFERENCE_GRAPH_SCHEMA_VERSION:
            raise ValueError(f"unsupported reference graph schema: {data.get('schema_version')!r}")
        rows = data.get("nodes")
        edges = data.get("edges")
        if not isinstance(rows, list) or not isinstance(edges, list):
            raise ValueError("reference graph nodes and edges must be lists")
        nodes = []
        for row in rows:
            if not isinstance(row, dict) or not row.get("id") or not row.get("kind"):
                raise ValueError("invalid reference node")
            nodes.append(ReferenceNode(dict(row)))
        parsed_edges = []
        allowed_confidence = {"verified", "derived", "candidate"}
        for row in edges:
            if not isinstance(row, dict):
                raise ValueError("invalid reference edge")
            if row.get("confidence") not in allowed_confidence:
                raise ValueError(f"invalid reference confidence: {row.get('confidence')!r}")
            parsed_edges.append(ReferenceEdge(dict(row)))
        metadata = {key: value for key, value in data.items() if key not in {"nodes", "edges"}}
        return cls(nodes, parsed_edges, metadata)

    def __len__(self):
        return len(self._nodes)

    def search(self, query="", kind=None, locale="zh_cn", issues_only=False):
        del locale  # all localized names are indexed together
        query = str(query or "").strip().casefold()
        kind = str(kind or "").strip()
        return tuple(
            node
            for node in self._nodes
            if (not kind or node.kind == kind)
            and (not issues_only or node.issue)
            and (not query or query in self._search_text[node.id])
        )

    def neighbors(self, node_id):
        if node_id not in self._by_id:
            return ()
        return tuple(
            ReferenceLink(edge, self._by_id[other_id], direction)
            for edge, other_id, direction in self._links[node_id]
        )

    def explain(self, node_id, locale="zh_cn"):
        del locale
        node = self._by_id.get(str(node_id))
        if node is None:
            return None
        return ReferenceExplanation(node=node, links=self.neighbors(node.id))

    def diagnostics(self):
        return dict(self.metadata.get("diagnostics", {}))


def load_default_reference_graph(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    try:
        return ReferenceGraph.load(root / "ao_reference_graph.json")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return ReferenceGraph()
