from app.domain.ontology_graph import OntologyGraph, refresh_ontology_graph
from app.domain.ontology_parser import parse_ontology, parse_ontology_ttl
from app.domain.one_record_schema import detect_entities, get_related
from app.models.source import Chunk, ChunkMetadata
from app.rag.reranker import rerank

SAMPLE_TTL = """
@prefix cargo: <https://onerecord.iata.org/ns/cargo#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .

cargo:LogisticsObject a owl:Class ;
    rdfs:label "Logistics Object" .

cargo:Shipment a owl:Class ;
    rdfs:subClassOf cargo:LogisticsObject ;
    rdfs:label "Shipment" .

cargo:Piece a owl:Class ;
    rdfs:subClassOf cargo:LogisticsObject ;
    rdfs:label "Piece" .

cargo:containedPieces a owl:ObjectProperty ;
    rdfs:domain cargo:Shipment ;
    rdfs:range cargo:Piece .
"""

SAMPLE_OWL = """<?xml version="1.0"?>
<rdf:RDF
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:cargo="https://onerecord.iata.org/ns/cargo#">
  <owl:Class rdf:about="https://onerecord.iata.org/ns/cargo#LogisticsObject">
    <rdfs:label>Logistics Object</rdfs:label>
  </owl:Class>
  <owl:Class rdf:about="https://onerecord.iata.org/ns/cargo#Shipment">
    <rdfs:subClassOf rdf:resource="https://onerecord.iata.org/ns/cargo#LogisticsObject"/>
    <rdfs:label>Shipment</rdfs:label>
  </owl:Class>
  <owl:Class rdf:about="https://onerecord.iata.org/ns/cargo#Piece">
    <rdfs:subClassOf rdf:resource="https://onerecord.iata.org/ns/cargo#LogisticsObject"/>
    <rdfs:label>Piece</rdfs:label>
  </owl:Class>
  <owl:ObjectProperty rdf:about="https://onerecord.iata.org/ns/cargo#containedPieces">
    <rdfs:domain rdf:resource="https://onerecord.iata.org/ns/cargo#Shipment"/>
    <rdfs:range rdf:resource="https://onerecord.iata.org/ns/cargo#Piece"/>
  </owl:ObjectProperty>
</rdf:RDF>
"""


def test_parse_ontology_ttl_extracts_classes_and_properties():
    classes, properties = parse_ontology_ttl(SAMPLE_TTL)
    class_names = {c.name for c in classes}
    assert {"LogisticsObject", "Shipment", "Piece"}.issubset(class_names)
    assert any(p.name == "containedPieces" and p.domain == "Shipment" for p in properties)


def test_parse_ontology_detects_rdfxml_from_owl_source_path():
    classes, properties = parse_ontology(SAMPLE_OWL, source_path="sample.owl")
    class_names = {c.name for c in classes}
    assert {"LogisticsObject", "Shipment", "Piece"}.issubset(class_names)
    assert any(p.name == "containedPieces" and p.range == "Piece" for p in properties)


def test_ontology_graph_relates_shipment_and_piece():
    graph = OntologyGraph.from_ttl(SAMPLE_TTL)
    assert "Piece" in graph.get_related("Shipment")
    assert "Shipment" in graph.get_related("Piece")
    assert "LogisticsObject" in graph.get_related("Piece")


def test_get_related_prefers_ontology_graph():
    refresh_ontology_graph("data/raw")
    related = get_related("Shipment")
    assert "Piece" in related


def test_detect_entities_uses_ontology_vocabulary():
    refresh_ontology_graph("data/raw")
    found = detect_entities("Explain Shipment and Piece in ONE Record")
    assert "Shipment" in found
    assert "Piece" in found
    assert not any(entity.startswith("n") and entity[1:].isalnum() for entity in found)


def test_rerank_boosts_matching_entity_chunk():
    piece_chunk = Chunk(
        chunk_id="piece::1",
        content="Class definition: Piece",
        metadata=ChunkMetadata(source_name="ontology", entity="Piece"),
    )
    generic_chunk = Chunk(
        chunk_id="glossary::1",
        content="General glossary entry",
        metadata=ChunkMetadata(source_name="glossary"),
    )
    ranked = rerank("What is a Piece in ONE Record?", [generic_chunk, piece_chunk])
    assert ranked[0].metadata.entity == "Piece"


def test_rerank_prefers_property_chunks_for_ontology_queries():
    property_chunk = Chunk(
        chunk_id="prop::1",
        content="Property Definition: containedPieces",
        metadata=ChunkMetadata(
            source_name="ontology",
            chunk_type="property_definition",
            entity="containedPieces",
            related_entities=["Shipment", "Piece"],
        ),
    )
    generic_chunk = Chunk(
        chunk_id="docs::1",
        content="General ontology overview",
        metadata=ChunkMetadata(source_name="docs", chunk_type="concept"),
    )
    ranked = rerank(
        "What properties connect Shipment to Piece in the ONE Record ontology?",
        [generic_chunk, property_chunk],
    )
    assert ranked[0].metadata.chunk_type == "property_definition"


def test_rerank_preserves_vector_order_without_entities():
    """AUD-03: non-entity queries must keep the vector-ranked order."""
    chunks = [
        Chunk(
            chunk_id=f"docs::{i}",
            content=f"Docker compose setup step {i}",
            metadata=ChunkMetadata(source_name="ne_one", chunk_type="concept"),
        )
        for i in range(5)
    ]
    ranked = rerank("How do I start NE:ONE locally with docker compose?", chunks)
    assert [c.chunk_id for c in ranked] == [c.chunk_id for c in chunks]


def test_rerank_entity_boost_cannot_drag_distant_chunk_to_first():
    """AUD-03: entity boosts must not override a clearly better vector hit.

    A matching ontology chunk sitting near the bottom of a 10-candidate pool
    must not leapfrog the vector leader — boosts only nudge nearby ranks.
    """
    leader = Chunk(
        chunk_id="docs::piece-overview",
        content="Piece is a physical package in ONE Record logistics.",
        metadata=ChunkMetadata(source_name="docs", chunk_type="concept"),
    )
    fillers = [
        Chunk(
            chunk_id=f"docs::filler-{i}",
            content=f"Background logistics note {i}",
            metadata=ChunkMetadata(source_name="docs", chunk_type="concept"),
        )
        for i in range(7)
    ]
    distant_match = Chunk(
        chunk_id="ontology::piece",
        content="Class definition: Piece",
        metadata=ChunkMetadata(
            source_name="ontology",
            chunk_type="class_definition",
            entity="Piece",
            version="2023-12",
        ),
    )
    pool = [leader, *fillers, distant_match]
    assert len(pool) == 9
    ranked = rerank("What is a Piece in ONE Record?", pool)
    assert ranked[0].chunk_id == leader.chunk_id
    # Still present, just not forced to rank 1 from the bottom of the pool.
    assert distant_match.chunk_id in {c.chunk_id for c in ranked}
