"""Template-based JSON-LD example generator (SPEC section 10.2).

The LLM does NOT generate the raw structure — these templates do, so the
shape is always valid and stable. The @context points to the ONE Record
cargo ontology namespace. Examples are illustrative, not official payloads.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable

ONE_RECORD_CONTEXT = "https://onerecord.iata.org/ns/cargo"
_BASE = "https://example.com/logistics-objects"


def _new_id(kind: str) -> str:
    return f"{_BASE}/{kind}/{uuid.uuid4()}"


def generate_piece_example() -> dict[str, Any]:
    return {
        "@context": ONE_RECORD_CONTEXT,
        "@type": "Piece",
        "@id": _new_id("piece"),
        "goodsDescription": "Spare machine parts",
        "grossWeight": {"@type": "Value", "unit": "KGM", "value": 12.5},
        "dimensions": {
            "@type": "Dimensions",
            "length": {"@type": "Value", "unit": "CMT", "value": 40},
            "width": {"@type": "Value", "unit": "CMT", "value": 30},
            "height": {"@type": "Value", "unit": "CMT", "value": 25},
        },
        "containedItems": [],
    }


def generate_shipment_example() -> dict[str, Any]:
    return {
        "@context": ONE_RECORD_CONTEXT,
        "@type": "Shipment",
        "@id": _new_id("shipment"),
        "totalGrossWeight": {"@type": "Value", "unit": "KGM", "value": 12.5},
        "totalPieceCount": 1,
        "containedPieces": [{"@id": _new_id("piece")}],
        "shipmentWaybill": {"@id": _new_id("waybill")},
    }


def generate_waybill_example() -> dict[str, Any]:
    return {
        "@context": ONE_RECORD_CONTEXT,
        "@type": "Waybill",
        "@id": _new_id("waybill"),
        "waybillNumber": "020-12345678",
        "waybillType": "Master",
        "shipment": {"@id": _new_id("shipment")},
    }


def generate_transport_movement_example() -> dict[str, Any]:
    return {
        "@context": ONE_RECORD_CONTEXT,
        "@type": "TransportMovement",
        "@id": _new_id("transport-movement"),
        "modeCode": "Air",
        "departureLocation": {"@type": "Location", "code": "FRA"},
        "arrivalLocation": {"@type": "Location", "code": "SIN"},
    }


GENERATORS: dict[str, Callable[[], dict[str, Any]]] = {
    "Piece": generate_piece_example,
    "Shipment": generate_shipment_example,
    "Waybill": generate_waybill_example,
    "TransportMovement": generate_transport_movement_example,
}


def generate_for_entity(entity: str | None) -> dict[str, Any] | None:
    """Return a JSON-LD example for the entity, defaulting to Piece."""
    if entity and entity in GENERATORS:
        return GENERATORS[entity]()
    return generate_piece_example()


def generate_synthetic_batch(
    object_type: str,
    count: int,
    *,
    with_pieces: bool = False,
) -> dict[str, Any]:
    """Build one or more template JSON-LD objects for local synthetic mode.

    A single object is returned as a plain JSON-LD document. Multiple objects
    (or shipment+piece pairs) are wrapped in ``@graph`` so the existing
    JSON-LD canvas can render them without treating the payload as a workflow.
    """
    kind = object_type if object_type in GENERATORS else "Piece"
    n = max(1, min(int(count), 50))
    objects: list[dict[str, Any]] = []

    for _ in range(n):
        if kind == "Shipment" and with_pieces:
            piece = generate_piece_example()
            shipment = generate_shipment_example()
            shipment["containedPieces"] = [{"@id": piece["@id"]}]
            shipment["totalPieceCount"] = 1
            objects.append(shipment)
            objects.append(piece)
        else:
            objects.append(GENERATORS[kind]())

    if len(objects) == 1:
        return objects[0]
    return {
        "@context": ONE_RECORD_CONTEXT,
        "@graph": objects,
    }
