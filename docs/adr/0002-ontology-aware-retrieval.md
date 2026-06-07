# ADR 0002: Ontology-aware retrieval

## Status
Accepted (v0.2.1)

## Context
v0.1 retrieval is pure vector search over embedded chunks plus a **manually
curated** relationship map in `domain/one_record_schema.py`. That works for
demos but:

- `related_entities` on ontology chunks are often empty after ingest.
- Relationship questions depend on a static dict, not parsed OWL structure.
- Vector search alone may rank glossary/API chunks above the best ontology
  class definition for entity-specific questions.

`data/raw/ontology/one_record_core.ttl` is already chunked per class/property
via rdflib in `rag/chunker.py`, but the **graph structure** (subClassOf,
object property domain/range) is not used at retrieval time.

## Decision

### 1. OntologyGraph (in-memory)
- Add `domain/ontology_parser.py` to parse TTL into `OntologyClass` and
  `OntologyProperty` records.
- Add `domain/ontology_graph.py` to expose:
  - `get_related(entity)` — neighbors via subClassOf + object properties
  - `all_entity_names()` — for entity detection
  - `build_from_ttl(text)` / `load_from_directory(data/raw)`
- Refresh the graph on every `/ingest` from all `.ttl`/`.owl` files under
  `data/raw`.

### 2. Richer chunk metadata at ingest
- When chunking ontology documents, set `metadata.related_entities` from
  `OntologyGraph.get_related(entity)` for each class/property chunk.
- Qdrant payload already stores `related_entities`; no schema migration.

### 3. Entity-first reranking (not replacement retrieval)
- Keep **vector search** as the candidate generator (baseline recall).
- Fetch a **candidate pool** of `top_k * 3` (capped at 20) in `pipeline.py`.
- Implement boosting in `rag/reranker.py` (the v0.1 no-op seam):
  - Detect entities in the query (`one_record_schema.detect_entities`, augmented
    with ontology entity names).
  - Boost chunks whose `metadata.entity` matches a query entity.
  - Boost chunks linked via `related_entities` or ontology neighbors.
  - Preserve original vector order as tie-breaker.
- Return the top `rag_top_k` after rerank.

### 4. Graceful fallback
- If ontology parsing fails or yields zero classes, log a warning and keep
  v0.1 behavior (manual `ONE_RECORD_RELATIONSHIPS` + vector-only order).
- Offline mode, provider abstraction, and `/chat` JSON contract are unchanged.

## Alternatives considered

| Option | Why not (for v0.2.1) |
|--------|----------------------|
| Metadata-only Qdrant filter | Fragile when entity field missing on glossary/API chunks |
| Replace vector search with graph traversal | Loses lexical/API recall; bigger change |
| Full official IATA ontology in repo | Out of scope; illustrative TTL subset is enough for v0.2.1 |

## Consequences
- Relationship and concept questions should rank ontology class chunks higher.
- `related_concepts` in `/chat` prefer ontology neighbors, fall back to manual map.
- `reranker.py` is no longer a no-op; eval and tests must cover boost behavior.
- v0.2.2+ can extend the same graph for RecordForge entity validation.

## References
- `data/raw/ontology/one_record_core.ttl`
- `backend/app/rag/chunker.py` (`_chunk_ontology`)
- `backend/app/domain/one_record_schema.py`
- `docs/v0.2_development_plan.md` § v0.2.1
