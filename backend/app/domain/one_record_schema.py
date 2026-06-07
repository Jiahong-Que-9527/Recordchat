"""ONE Record entity relationships (SPEC section 10.1).

v0.2.1 prefers parsed ontology neighbors (ADR 0002) and falls back to the
curated map when the ontology graph is unavailable.
"""

from __future__ import annotations

from app.domain.ontology_graph import get_ontology_graph

ONE_RECORD_RELATIONSHIPS: dict[str, list[str]] = {
    "Shipment": ["Piece", "Waybill", "LogisticsEvent"],
    "Piece": ["Shipment", "LogisticsObject", "TransportMovement"],
    "Waybill": ["Shipment"],
    "LogisticsObject": ["Piece", "Shipment", "Waybill"],
    "TransportMovement": ["Piece", "LogisticsEvent", "Location"],
    "LogisticsEvent": ["Shipment", "Piece", "TransportMovement"],
    "Booking": ["Shipment", "TransportMovement"],
}

# Known ONE Record entity names (used for lightweight entity detection).
KNOWN_ENTITIES: list[str] = sorted(
    {
        *ONE_RECORD_RELATIONSHIPS.keys(),
        *(e for vs in ONE_RECORD_RELATIONSHIPS.values() for e in vs),
        "Product",
        "Company",
        "Location",
        "Item",
        "ULD",
        "Sensor",
        "Subscription",
        "Notification",
    }
)


def get_related(entity: str) -> list[str]:
    graph = get_ontology_graph()
    if graph and graph.has_entity(entity):
        related = graph.get_related(entity)
        if related:
            return related
    return ONE_RECORD_RELATIONSHIPS.get(entity, [])


def _entity_vocabulary() -> list[str]:
    names = set(KNOWN_ENTITIES)
    graph = get_ontology_graph()
    if graph:
        names.update(graph.all_entity_names())
    return sorted(names, key=len, reverse=True)


def detect_entities(text: str) -> list[str]:
    """Return known ONE Record entities mentioned in the text (case-insensitive)."""
    low = text.lower()
    found = []
    for ent in _entity_vocabulary():
        if ent.lower() in low and ent not in found:
            found.append(ent)
    return found
