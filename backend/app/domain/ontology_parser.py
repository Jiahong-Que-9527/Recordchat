"""Parse ONE Record ontology serializations into structured class/property records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rdflib import RDF, RDFS, BNode, Graph, OWL


@dataclass(frozen=True)
class OntologyClass:
    name: str
    label: str | None
    comment: str | None
    superclasses: tuple[str, ...]


@dataclass(frozen=True)
class OntologyProperty:
    name: str
    label: str | None
    comment: str | None
    domain: str | None
    range: str | None
    is_object_property: bool


def _local_name(uri) -> str:
    s = str(uri)
    return s.rsplit("#", 1)[-1].rsplit("/", 1)[-1] or s


def _is_named_node(node) -> bool:
    return node is not None and not isinstance(node, BNode)


def _literal_value(graph: Graph, subject, predicate) -> str | None:
    value = graph.value(subject, predicate)
    if value is None:
        return None
    return str(value)


def _infer_rdf_format(text: str, source_path: str | None = None) -> str:
    if source_path:
        suffix = Path(source_path).suffix.lower()
        if suffix == ".owl":
            return "xml"
        if suffix == ".ttl":
            return "turtle"

    stripped = text.lstrip()
    if stripped.startswith("<?xml") or stripped.startswith("<rdf:RDF"):
        return "xml"
    return "turtle"


def parse_ontology(
    text: str,
    *,
    source_path: str | None = None,
    rdf_format: str | None = None,
) -> tuple[list[OntologyClass], list[OntologyProperty]]:
    """Parse ontology text into classes and properties."""
    graph = Graph()
    graph.parse(data=text, format=rdf_format or _infer_rdf_format(text, source_path))

    classes: list[OntologyClass] = []
    seen_classes: set[str] = set()

    class_subjects = list(graph.subjects(RDF.type, OWL.Class)) + list(
        graph.subjects(RDF.type, RDFS.Class)
    )
    for subj in class_subjects:
        if not _is_named_node(subj):
            continue
        name = _local_name(subj)
        if name in seen_classes:
            continue
        seen_classes.add(name)
        supers = tuple(
            sorted(
                {
                    _local_name(s)
                    for s in graph.objects(subj, RDFS.subClassOf)
                    if _is_named_node(s)
                    if str(s) != str(RDFS.Resource)
                }
            )
        )
        classes.append(
            OntologyClass(
                name=name,
                label=_literal_value(graph, subj, RDFS.label),
                comment=_literal_value(graph, subj, RDFS.comment),
                superclasses=supers,
            )
        )

    properties: list[OntologyProperty] = []
    seen_props: set[str] = set()
    prop_types = [OWL.ObjectProperty, OWL.DatatypeProperty, RDF.Property]

    for prop_type in prop_types:
        for subj in graph.subjects(RDF.type, prop_type):
            if not _is_named_node(subj):
                continue
            name = _local_name(subj)
            if name in seen_props:
                continue
            seen_props.add(name)
            domain = graph.value(subj, RDFS.domain)
            range_ = graph.value(subj, RDFS.range)
            properties.append(
                OntologyProperty(
                    name=name,
                    label=_literal_value(graph, subj, RDFS.label),
                    comment=_literal_value(graph, subj, RDFS.comment),
                    domain=_local_name(domain) if _is_named_node(domain) else None,
                    range=_local_name(range_) if _is_named_node(range_) else None,
                    is_object_property=prop_type == OWL.ObjectProperty,
                )
            )

    return classes, properties


def parse_ontology_ttl(text: str) -> tuple[list[OntologyClass], list[OntologyProperty]]:
    """Backward-compatible turtle-only parser wrapper."""
    return parse_ontology(text, rdf_format="turtle")
