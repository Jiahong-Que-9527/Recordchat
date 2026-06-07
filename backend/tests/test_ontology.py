from app.domain.ontology_graph import OntologyGraph, refresh_ontology_graph
from app.domain.ontology_parser import parse_ontology_ttl
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


def test_parse_ontology_ttl_extracts_classes_and_properties():
    classes, properties = parse_ontology_ttl(SAMPLE_TTL)
    class_names = {c.name for c in classes}
    assert {"LogisticsObject", "Shipment", "Piece"}.issubset(class_names)
    assert any(p.name == "containedPieces" and p.domain == "Shipment" for p in properties)


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
