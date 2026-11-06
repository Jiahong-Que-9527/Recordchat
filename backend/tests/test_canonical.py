"""AUD-02 / #27: canonical source version policy.

[房玄龄·2026-11-06] Authored fixtures keep CI independent of local corpora.
"""

import json
from pathlib import Path

import pytest

from app.core.config import Settings
from app.rag.canonical import is_canonical_source

@pytest.fixture
def raw(tmp_path, monkeypatch):
    """Create source-family names and metadata without redistributing real sources."""
    root = tmp_path / "raw"
    files = {
        "ontology/official/one_record_data_model.2025-07.ttl": ("2025-07", "ontology"),
        "ontology/official/one_record_data_model.2023-12.ttl": ("2023-12", "ontology"),
        "ontology/official/one_record_data_model.working_draft.ttl": ("working_draft", "ontology"),
        "ontology/official/one_record_api_ontology.current.ttl": ("current", "ontology"),
        "ontology/official/one_record_api_ontology.current.owl": ("current", "ontology"),
        "api_specs/official/ONE-Record-API-OpenAPI.2024-12.yaml": ("2024-12", "api_spec"),
        "api_specs/official/ONE-Record-API-OpenAPI.2023-12.yaml": ("2023-12", "api_spec"),
        "one_record_docs/spec_development/overview.md": ("development", "docs"),
        "one_record_docs/spec_2025_07/overview.md": ("2025-07", "docs"),
        "one_record_docs/spec_2023_12/overview.md": ("2023-12", "docs"),
        "one_record_docs/spec_2025_07/nested/ontology.ttl": ("2025-07", "ontology"),
        "api_specs/ne_one/ontologies/IATA-1R-DM-Ontology.ttl": ("2025-07", "ontology"),
        "api_specs/ne_one/ontologies/ONE-Record-API-Ontology.ttl": ("current", "ontology"),
        "api_specs/ne_one/ontologies/NEONE-DM.ttl": ("fixture", "ontology"),
    }
    for relative, (version, document_type) in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        # The loader reads text/sidecars; these are authored synthetic bodies.
        path.write_text("Authored canonical-policy test fixture.\n", encoding="utf-8")
        sidecar = {
            "source_name": "Authored canonical-policy test fixture",
            "version": version,
            "url": "https://example.invalid/canonical-policy-fixture",
            "document_type": document_type,
        }
        path.with_suffix(path.suffix + ".meta.json").write_text(
            json.dumps(sidecar), encoding="utf-8"
        )
    monkeypatch.setattr("app.rag.canonical.get_settings", _settings)
    return root


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        canonical_ontology_versions="2025-07",
        canonical_api_ontology_versions="current",
        canonical_openapi_versions="2024-12",
        canonical_spec_versions="development,2025-07",
    )


def test_canonical_keeps_pinned_ontology_and_skips_older_releases(raw):
    settings = _settings()
    keep = raw / "ontology/official/one_record_data_model.2025-07.ttl"
    skip_old = raw / "ontology/official/one_record_data_model.2023-12.ttl"
    skip_draft = raw / "ontology/official/one_record_data_model.working_draft.ttl"
    assert keep.exists() and skip_old.exists() and skip_draft.exists()
    assert is_canonical_source(keep, source_root=raw, settings=settings)
    assert not is_canonical_source(skip_old, source_root=raw, settings=settings)
    assert not is_canonical_source(skip_draft, source_root=raw, settings=settings)


def test_canonical_skips_owl_when_ttl_peer_exists(raw):
    settings = _settings()
    ttl = raw / "ontology/official/one_record_api_ontology.current.ttl"
    owl = raw / "ontology/official/one_record_api_ontology.current.owl"
    assert ttl.exists() and owl.exists()
    assert is_canonical_source(ttl, source_root=raw, settings=settings)
    assert not is_canonical_source(owl, source_root=raw, settings=settings)


def test_canonical_openapi_keeps_one_version(raw):
    settings = _settings()
    keep = raw / "api_specs/official/ONE-Record-API-OpenAPI.2024-12.yaml"
    skip = raw / "api_specs/official/ONE-Record-API-OpenAPI.2023-12.yaml"
    assert keep.exists() and skip.exists()
    assert is_canonical_source(keep, source_root=raw, settings=settings)
    assert not is_canonical_source(skip, source_root=raw, settings=settings)


def test_canonical_spec_keeps_development_and_2025_07_drops_2023_12(raw):
    settings = _settings()
    keep_dev = next((raw / "one_record_docs/spec_development").rglob("*.md"))
    keep_2025 = next((raw / "one_record_docs/spec_2025_07").rglob("*.md"))
    skip_2023 = next((raw / "one_record_docs/spec_2023_12").rglob("*.md"))
    assert is_canonical_source(keep_dev, source_root=raw, settings=settings)
    assert is_canonical_source(keep_2025, source_root=raw, settings=settings)
    assert not is_canonical_source(skip_2023, source_root=raw, settings=settings)


def test_canonical_skips_nested_ontology_extracts_under_specs(raw):
    settings = _settings()
    nested = list((raw / "one_record_docs/spec_2025_07").rglob("*.ttl"))
    assert nested, "expected nested ontology extract under spec_2025_07"
    assert not is_canonical_source(nested[0], source_root=raw, settings=settings)


def test_loader_skips_non_canonical_documents(raw):
    from app.rag.loader import load_documents

    docs = load_documents(str(raw))
    versions_by_path = {Path(d.path).name: d.metadata.version for d in docs}
    assert "one_record_data_model.2025-07.ttl" in versions_by_path
    assert "one_record_data_model.2023-12.ttl" not in versions_by_path
    assert "ONE-Record-API-OpenAPI.2024-12.yaml" in versions_by_path
    assert "ONE-Record-API-OpenAPI.2023-12.yaml" not in versions_by_path


def test_canonical_skips_ne_one_iata_ontology_mirrors_keeps_neone_specific(raw):
    settings = _settings()
    mirror = raw / "api_specs/ne_one/ontologies/IATA-1R-DM-Ontology.ttl"
    api_mirror = raw / "api_specs/ne_one/ontologies/ONE-Record-API-Ontology.ttl"
    keep = raw / "api_specs/ne_one/ontologies/NEONE-DM.ttl"
    assert mirror.exists() and api_mirror.exists() and keep.exists()
    assert not is_canonical_source(mirror, source_root=raw, settings=settings)
    assert not is_canonical_source(api_mirror, source_root=raw, settings=settings)
    assert is_canonical_source(keep, source_root=raw, settings=settings)
