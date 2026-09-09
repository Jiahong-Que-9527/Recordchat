"""AUD-02 / #27: canonical source version policy."""

from pathlib import Path

from app.core.config import Settings
from app.rag.canonical import is_canonical_source

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"


def _settings() -> Settings:
    return Settings(
        canonical_ontology_versions="2025-07",
        canonical_api_ontology_versions="current",
        canonical_openapi_versions="2024-12",
        canonical_spec_versions="development,2025-07",
    )


def test_canonical_keeps_pinned_ontology_and_skips_older_releases():
    settings = _settings()
    keep = RAW / "ontology/official/one_record_data_model.2025-07.ttl"
    skip_old = RAW / "ontology/official/one_record_data_model.2023-12.ttl"
    skip_draft = RAW / "ontology/official/one_record_data_model.working_draft.ttl"
    assert keep.exists() and skip_old.exists() and skip_draft.exists()
    assert is_canonical_source(keep, source_root=RAW, settings=settings)
    assert not is_canonical_source(skip_old, source_root=RAW, settings=settings)
    assert not is_canonical_source(skip_draft, source_root=RAW, settings=settings)


def test_canonical_skips_owl_when_ttl_peer_exists():
    settings = _settings()
    ttl = RAW / "ontology/official/one_record_api_ontology.current.ttl"
    owl = RAW / "ontology/official/one_record_api_ontology.current.owl"
    assert ttl.exists() and owl.exists()
    assert is_canonical_source(ttl, source_root=RAW, settings=settings)
    assert not is_canonical_source(owl, source_root=RAW, settings=settings)


def test_canonical_openapi_keeps_one_version():
    settings = _settings()
    keep = RAW / "api_specs/official/ONE-Record-API-OpenAPI.2024-12.yaml"
    skip = RAW / "api_specs/official/ONE-Record-API-OpenAPI.2023-12.yaml"
    assert keep.exists() and skip.exists()
    assert is_canonical_source(keep, source_root=RAW, settings=settings)
    assert not is_canonical_source(skip, source_root=RAW, settings=settings)


def test_canonical_spec_keeps_development_and_2025_07_drops_2023_12():
    settings = _settings()
    keep_dev = next((RAW / "one_record_docs/spec_development").rglob("*.md"))
    keep_2025 = next((RAW / "one_record_docs/spec_2025_07").rglob("*.md"))
    skip_2023 = next((RAW / "one_record_docs/spec_2023_12").rglob("*.md"))
    assert is_canonical_source(keep_dev, source_root=RAW, settings=settings)
    assert is_canonical_source(keep_2025, source_root=RAW, settings=settings)
    assert not is_canonical_source(skip_2023, source_root=RAW, settings=settings)


def test_canonical_skips_nested_ontology_extracts_under_specs():
    settings = _settings()
    nested = list((RAW / "one_record_docs/spec_2025_07").rglob("*.ttl"))
    assert nested, "expected nested ontology extract under spec_2025_07"
    assert not is_canonical_source(nested[0], source_root=RAW, settings=settings)


def test_loader_skips_non_canonical_documents():
    from app.rag.loader import load_documents

    docs = load_documents(str(RAW))
    versions_by_path = {Path(d.path).name: d.metadata.version for d in docs}
    assert "one_record_data_model.2025-07.ttl" in versions_by_path
    assert "one_record_data_model.2023-12.ttl" not in versions_by_path
    assert "ONE-Record-API-OpenAPI.2024-12.yaml" in versions_by_path
    assert "ONE-Record-API-OpenAPI.2023-12.yaml" not in versions_by_path


def test_canonical_skips_ne_one_iata_ontology_mirrors_keeps_neone_specific():
    settings = _settings()
    mirror = RAW / "api_specs/ne_one/ontologies/IATA-1R-DM-Ontology.ttl"
    api_mirror = RAW / "api_specs/ne_one/ontologies/ONE-Record-API-Ontology.ttl"
    keep = RAW / "api_specs/ne_one/ontologies/NEONE-DM.ttl"
    assert mirror.exists() and api_mirror.exists() and keep.exists()
    assert not is_canonical_source(mirror, source_root=RAW, settings=settings)
    assert not is_canonical_source(api_mirror, source_root=RAW, settings=settings)
    assert is_canonical_source(keep, source_root=RAW, settings=settings)
