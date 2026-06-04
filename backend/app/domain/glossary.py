"""Curated ONE Record seed knowledge (SPEC section 5.2).

This is the graceful-degradation knowledge base: even when data/raw/ is
empty (or there is no network access to scrape IATA sources), `/ingest`
loads these entries into Qdrant so `/chat` works out of the box.

Definitions are intentionally concise and paraphrased for educational use.
They are marked as the "RecordChat curated glossary" source so the UI can
distinguish them from official IATA documentation once that is ingested.
"""

from __future__ import annotations

from app.models.source import Chunk, ChunkMetadata

GLOSSARY_SOURCE = "RecordChat curated glossary"

# entity -> (definition, related_entities)
GLOSSARY: dict[str, dict] = {
    "ONE Record": {
        "definition": (
            "ONE Record is an IATA data sharing standard for the air cargo "
            "industry. It defines a single, shared record of truth for a "
            "shipment, modeled as a web of interlinked data (logistics "
            "objects) accessed via a standard REST API and expressed as "
            "JSON-LD / linked data."
        ),
        "related": ["LogisticsObject", "Shipment", "JSON-LD"],
    },
    "LogisticsObject": {
        "definition": (
            "A LogisticsObject is the base class for all data entities in "
            "ONE Record. Each logistics object has a unique URI/@id, is "
            "exposed through a ONE Record Server, and links to other logistics "
            "objects via linked-data references. Shipment, Piece, Waybill, etc. "
            "are all kinds of LogisticsObject."
        ),
        "related": ["Shipment", "Piece", "Waybill", "ONE Record"],
    },
    "Shipment": {
        "definition": (
            "A Shipment represents the transport of goods from a shipper to a "
            "consignee under a single Waybill. It groups one or more Pieces and "
            "carries shipment-level information such as parties, routing, and "
            "totals."
        ),
        "related": ["Piece", "Waybill", "LogisticsEvent"],
    },
    "Piece": {
        "definition": (
            "A Piece represents the smallest physical, individually "
            "identifiable unit of goods in ONE Record (for example a single "
            "package or item). Pieces belong to a Shipment and can carry "
            "details such as dimensions, weight, and goods description."
        ),
        "related": ["Shipment", "LogisticsObject", "TransportMovement"],
    },
    "Waybill": {
        "definition": (
            "A Waybill (Air Waybill / AWB) is the transport document/contract "
            "for a Shipment. In ONE Record it is modeled as a LogisticsObject "
            "that references its Shipment and carries the AWB number and "
            "contractual parties."
        ),
        "related": ["Shipment"],
    },
    "TransportMovement": {
        "definition": (
            "A TransportMovement describes the physical movement of cargo "
            "between locations on a means of transport (e.g. a flight leg), "
            "including departure/arrival locations and times."
        ),
        "related": ["Piece", "LogisticsEvent", "Location"],
    },
    "LogisticsEvent": {
        "definition": (
            "A LogisticsEvent captures something that happened to a logistics "
            "object at a point in time (status changes, milestones), enabling "
            "tracking and an audit trail across the shipment lifecycle."
        ),
        "related": ["Shipment", "Piece", "TransportMovement"],
    },
    "Booking": {
        "definition": (
            "A Booking represents a request and agreement to transport cargo, "
            "capturing the planned routing and capacity prior to actual "
            "shipment execution."
        ),
        "related": ["Shipment", "TransportMovement"],
    },
    "Product": {
        "definition": (
            "A Product describes the nature of the goods being shipped "
            "(commodity, characteristics, handling requirements) and is "
            "referenced by Items/Pieces."
        ),
        "related": ["Piece", "Item"],
    },
    "Company": {
        "definition": (
            "A Company models an organization acting as a party in the supply "
            "chain (shipper, consignee, carrier, forwarder, handling agent). "
            "It is referenced from shipments, waybills, and bookings."
        ),
        "related": ["Shipment", "Waybill", "Booking"],
    },
    "Location": {
        "definition": (
            "A Location models a place relevant to logistics (airport, "
            "warehouse, address) and is referenced by transport movements and "
            "events to express where things happen."
        ),
        "related": ["TransportMovement", "LogisticsEvent"],
    },
    "Item": {
        "definition": (
            "An Item represents a quantity of a given Product within a Piece, "
            "linking the physical unit to the description of the goods it "
            "contains."
        ),
        "related": ["Piece", "Product"],
    },
    "ULD": {
        "definition": (
            "A ULD (Unit Load Device) is a container or pallet used to "
            "consolidate cargo for air transport. In ONE Record it can group "
            "pieces and is tracked as part of transport operations."
        ),
        "related": ["Piece", "TransportMovement"],
    },
    "Sensor": {
        "definition": (
            "A Sensor models a measuring device attached to cargo or a ULD "
            "(temperature, humidity, shock), producing measurements that can be "
            "linked to logistics objects for monitoring."
        ),
        "related": ["Piece", "ULD"],
    },
    "Subscription": {
        "definition": (
            "A Subscription is the ONE Record mechanism by which a party "
            "registers interest in updates to a logistics object. When the "
            "object changes, the server sends Notifications to subscribers "
            "(publish/subscribe over the API)."
        ),
        "related": ["Notification", "LogisticsObject"],
    },
    "Notification": {
        "definition": (
            "A Notification is a message pushed by a ONE Record Server to "
            "subscribers when a relevant logistics object is created or "
            "updated, enabling event-driven data sharing."
        ),
        "related": ["Subscription", "LogisticsEvent"],
    },
    "JSON-LD": {
        "definition": (
            "JSON-LD (JSON for Linking Data) is the serialization format used "
            "by ONE Record. It adds an @context (mapping terms to ontology "
            "IRIs), @type (the class), and @id (the object's URI) to plain "
            "JSON, turning documents into linked, machine-interpretable data."
        ),
        "related": ["LogisticsObject", "ONE Record"],
    },
}


def glossary_chunks() -> list[Chunk]:
    """Materialize the glossary as retrievable chunks."""
    chunks: list[Chunk] = []
    for entity, info in GLOSSARY.items():
        content = f"{entity}: {info['definition']}"
        chunks.append(
            Chunk(
                chunk_id=f"glossary::{entity}",
                content=content,
                metadata=ChunkMetadata(
                    source_name=GLOSSARY_SOURCE,
                    section_title=entity,
                    chunk_type="concept",
                    entity=entity,
                    related_entities=list(info.get("related", [])),
                ),
            )
        )
    return chunks
