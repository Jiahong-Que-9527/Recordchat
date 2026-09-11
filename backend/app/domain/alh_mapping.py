"""AviationLakehouse Bronze / Silver / Gold mapping helpers (#8).

Project narrative only — no LLM calls, no HTTP, no live lakehouse.
Summaries must stay aligned with
``data/raw/one_record_docs/aviation_lakehouse.md``.
"""

from __future__ import annotations

from typing import Literal

from app.domain import one_record_schema

LayerName = Literal["bronze", "silver", "gold"]

_MAPPED_ENTITIES: tuple[str, ...] = (
    "Piece",
    "Shipment",
    "Waybill",
    "TransportMovement",
    "LogisticsEvent",
)

_GENERIC_LAYERS: tuple[dict[str, str], ...] = (
    {
        "layer": "bronze",
        "summary": (
            "Bronze lands raw or near-raw ONE Record JSON-LD LogisticsObjects "
            "as received, preserving @id, @type, and source metadata for audit "
            "and replay."
        ),
        "example_landing": (
            "Append the original JSON-LD document with an ingest timestamp and "
            "upstream Server URI; do not reshape business keys yet."
        ),
    },
    {
        "layer": "silver",
        "summary": (
            "Silver stores typed, validated logistics entities at object grain "
            "(Piece, Shipment, Waybill, TransportMovement, LogisticsEvent) with "
            "conformed identifiers and joinable links."
        ),
        "example_landing": (
            "Parse @type, normalize @id-derived keys, and materialize links such "
            "as Shipment → contained Pieces for analytical joins."
        ),
    },
    {
        "layer": "gold",
        "summary": (
            "Gold holds business-ready facts and aggregates (cycle time, dwell, "
            "event timelines). It supports analytics and is not the operational "
            "system of record."
        ),
        "example_landing": (
            "Publish metrics that cite logistics-object ids without minting new "
            "authoritative ONE Record state in the lakehouse."
        ),
    },
)

_ENTITY_LAYERS: dict[str, tuple[dict[str, str], ...]] = {
    "Piece": (
        {
            "layer": "bronze",
            "summary": (
                "Land each Piece JSON-LD document (or change event) as received, "
                "keeping dimensions, weight, and @id intact."
            ),
            "example_landing": (
                "Store the raw Piece payload plus source Server URI so the "
                "physical unit can be re-parsed later."
            ),
        },
        {
            "layer": "silver",
            "summary": (
                "Validate @type=Piece, conform the Piece id, and link it to its "
                "parent Shipment when containment references exist."
            ),
            "example_landing": (
                "Expose a Piece row with shipment_id, gross weight, and goods "
                "description ready for joins."
            ),
        },
        {
            "layer": "gold",
            "summary": (
                "Derive piece-level facts such as dwell between logistics events "
                "or time-in-status along the journey."
            ),
            "example_landing": (
                "A Gold fact might be piece_dwell_hours keyed by piece_id and "
                "milestone pair."
            ),
        },
    ),
    "Shipment": (
        {
            "layer": "bronze",
            "summary": (
                "Land the Shipment JSON-LD document with containedPieces links "
                "exactly as published by the upstream Server."
            ),
            "example_landing": (
                "Keep the original Shipment body, including party and totals "
                "fields, without exploding nested pieces yet."
            ),
        },
        {
            "layer": "silver",
            "summary": (
                "Type the Shipment, conform its id, and materialize piece "
                "containment so analysts can count and join child Pieces."
            ),
            "example_landing": (
                "Shipment silver table plus a shipment_piece bridge built from "
                "containedPieces."
            ),
        },
        {
            "layer": "gold",
            "summary": (
                "Compute shipment cycle time, pieces-per-shipment, and other "
                "lane or party aggregates for reporting."
            ),
            "example_landing": (
                "Gold metrics such as shipment_cycle_hours from booking or first "
                "event to delivery milestone."
            ),
        },
    ),
    "Waybill": (
        {
            "layer": "bronze",
            "summary": (
                "Land Waybill JSON-LD as received, preserving AWB number and "
                "contractual party references."
            ),
            "example_landing": (
                "Raw Waybill document keyed by @id with unchanged waybillNumber."
            ),
        },
        {
            "layer": "silver",
            "summary": (
                "Validate @type=Waybill and link it to its Shipment for "
                "document-centric joins."
            ),
            "example_landing": (
                "Waybill silver row with shipment_id and normalized AWB number."
            ),
        },
        {
            "layer": "gold",
            "summary": (
                "Use Waybill attributes as dimensions on shipment facts (for "
                "example by AWB or contracting party)."
            ),
            "example_landing": (
                "Gold reports sliced by waybillNumber without treating the lake "
                "as the AWB system of record."
            ),
        },
    ),
    "TransportMovement": (
        {
            "layer": "bronze",
            "summary": (
                "Land TransportMovement JSON-LD legs with departure/arrival "
                "locations and times as published."
            ),
            "example_landing": (
                "Raw movement documents retained for replay of routing changes."
            ),
        },
        {
            "layer": "silver",
            "summary": (
                "Type each movement, conform ids, and link movements to the "
                "pieces or shipments they carry when references exist."
            ),
            "example_landing": (
                "Movement silver rows with origin, destination, and linked "
                "logistics-object ids."
            ),
        },
        {
            "layer": "gold",
            "summary": (
                "Derive lane performance and transit-time facts from cleaned "
                "movement histories."
            ),
            "example_landing": (
                "Gold transit_hours by origin–destination pair citing movement "
                "ids."
            ),
        },
    ),
    "LogisticsEvent": (
        {
            "layer": "bronze",
            "summary": (
                "Land LogisticsEvent payloads as an append-only milestone and "
                "status stream tied to logistics objects."
            ),
            "example_landing": (
                "Raw event documents with event time, event code, and target "
                "object @id."
            ),
        },
        {
            "layer": "silver",
            "summary": (
                "Validate events, conform object references, and order them into "
                "per-object timelines."
            ),
            "example_landing": (
                "Event silver table keyed by event_id with logistics_object_id "
                "and normalized event_time."
            ),
        },
        {
            "layer": "gold",
            "summary": (
                "Build event timelines and milestone SLAs used by dwell and "
                "cycle-time metrics."
            ),
            "example_landing": (
                "Gold timeline facts such as time_between_milestones for a Piece "
                "or Shipment."
            ),
        },
    ),
}


def mapped_entities() -> tuple[str, ...]:
    """Entities with explicit Bronze / Silver / Gold notes."""
    return _MAPPED_ENTITIES


def get_alh_layers(entity: str) -> list[dict]:
    """Return bronze → silver → gold dicts for a known entity, else []."""
    layers = _ENTITY_LAYERS.get(entity)
    if not layers:
        return []
    return [dict(layer) for layer in layers]


def format_alh_context(query: str) -> str:
    """Plain-text mapping notes for prompt enrichment."""
    lines: list[str] = [
        "RecordChat AviationLakehouse narrative (not an IATA product):",
        "Bronze = raw landed JSON-LD; Silver = typed linked entities; "
        "Gold = analytical facts (not the system of record).",
    ]
    for layer in _GENERIC_LAYERS:
        lines.append(
            f"- {layer['layer'].title()}: {layer['summary']} "
            f"Example: {layer['example_landing']}"
        )

    entities = [
        ent for ent in one_record_schema.detect_entities(query) if ent in _ENTITY_LAYERS
    ]
    for ent in entities:
        lines.append(f"Entity-specific notes for {ent}:")
        for layer in get_alh_layers(ent):
            lines.append(
                f"  - {layer['layer'].title()}: {layer['summary']} "
                f"Example: {layer['example_landing']}"
            )
    return "\n".join(lines)
