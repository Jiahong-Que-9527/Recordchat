"""Manually curated ONE Record relationship map (SPEC section 10.1).

Used to enrich `related_concepts` for relationship questions. In v0.2 this
can be replaced/augmented by parsing the official ontology.
"""

from __future__ import annotations

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
    return ONE_RECORD_RELATIONSHIPS.get(entity, [])


def detect_entities(text: str) -> list[str]:
    """Return known ONE Record entities mentioned in the text (case-insensitive)."""
    low = text.lower()
    found = []
    for ent in KNOWN_ENTITIES:
        if ent.lower() in low:
            found.append(ent)
    return found
