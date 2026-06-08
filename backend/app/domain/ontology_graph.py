"""In-memory ONE Record ontology graph for entity-first retrieval (ADR 0002)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.core.logging import get_logger
from app.domain.ontology_parser import OntologyClass, OntologyProperty, parse_ontology

logger = get_logger(__name__)

_ONTOLOGY_EXTENSIONS = {".ttl", ".owl"}


def _should_skip_path(path: Path) -> bool:
    return "_staging" in path.parts


class OntologyGraph:
    """Adjacency view over parsed OWL classes and object properties."""

    def __init__(
        self,
        classes: list[OntologyClass],
        properties: list[OntologyProperty],
    ) -> None:
        self._classes = {c.name: c for c in classes}
        self._related: dict[str, set[str]] = defaultdict(set)

        for cls in classes:
            for sup in cls.superclasses:
                self._related[cls.name].add(sup)
                self._related[sup].add(cls.name)

        for prop in properties:
            if prop.is_object_property and prop.domain and prop.range:
                self._related[prop.domain].add(prop.range)
                self._related[prop.range].add(prop.domain)

    @property
    def class_count(self) -> int:
        return len(self._classes)

    def has_entity(self, entity: str) -> bool:
        return entity in self._classes or entity in self._related

    def all_entity_names(self) -> list[str]:
        names = set(self._classes)
        for related in self._related.values():
            names.update(related)
        return sorted(names)

    def get_related(self, entity: str) -> list[str]:
        return sorted(self._related.get(entity, set()))

    @classmethod
    def from_ttl(cls, text: str) -> OntologyGraph:
        classes, properties = parse_ontology(text, rdf_format="turtle")
        return cls(classes, properties)

    @classmethod
    def from_directory(cls, source_dir: str) -> OntologyGraph | None:
        root = Path(source_dir)
        if not root.exists():
            return None

        all_classes: list[OntologyClass] = []
        all_properties: list[OntologyProperty] = []
        parsed_files = 0

        for path in sorted(root.rglob("*")):
            if _should_skip_path(path):
                continue
            if not path.is_file() or path.suffix not in _ONTOLOGY_EXTENSIONS:
                continue
            try:
                text = path.read_text(encoding="utf-8")
                classes, properties = parse_ontology(text, source_path=str(path))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping unparseable ontology %s: %s", path, exc)
                continue
            all_classes.extend(classes)
            all_properties.extend(properties)
            parsed_files += 1

        if parsed_files == 0:
            return None

        graph = cls(all_classes, all_properties)
        logger.info(
            "OntologyGraph loaded: %d classes, %d property edges from %d file(s)",
            graph.class_count,
            sum(1 for p in all_properties if p.is_object_property and p.domain and p.range),
            parsed_files,
        )
        return graph


_graph: OntologyGraph | None = None


def get_ontology_graph() -> OntologyGraph | None:
    return _graph


def refresh_ontology_graph(source_dir: str = "data/raw") -> OntologyGraph | None:
    """Rebuild the singleton graph from ontology files under source_dir."""
    global _graph
    _graph = OntologyGraph.from_directory(source_dir)
    if _graph is None:
        logger.warning("No ontology graph loaded from %s; using manual fallbacks.", source_dir)
    return _graph
