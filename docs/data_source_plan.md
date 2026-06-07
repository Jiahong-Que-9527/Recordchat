# RecordChat Data Source Plan

This document is the execution plan for expanding the RecordChat knowledge base
to the required ONE Record and NE:ONE source set.

For direct source URLs and per-folder download instructions, also see:
[docs/data_download_guide.md](data_download_guide.md)

The key idea is simple:

1. not every source should be ingested the same way
2. the current loader only ingests text-like files under `data/raw`
3. some sources can be scripted, while some need manual download and curation

## 1. Current Ingestion Constraints

Today `backend/app/rag/loader.py` ingests these file types:

- `.ttl`
- `.owl`
- `.md`
- `.markdown`
- `.txt`
- `.json`
- `.jsonld`
- `.yaml`
- `.yml`

This means:

- HTML pages should be converted to Markdown before ingest
- PDFs should be converted to Markdown or plain text before ingest
- diagrams should be captured as image assets plus a manual text description
- source code should not be bulk-ingested; only README/docs/examples/configs/tests
  should be extracted into text-like files

## 2. Execution Order

The next work should follow this order:

1. `D0` Minimal source pack for "basically meets requirements"
2. `D1` Normalize and import sources into `data/raw`
3. `D2` Expand implementation knowledge with NE:ONE
4. `D3` Add ALH and broader narrative data
5. `D4` Add RecordForge-facing and community example data

## 3. Source Matrix

### D0 — Minimal source pack

These are the sources that should be in place before any more ambitious feature
work is treated as "complete enough".

| Source | Priority | When | How to obtain | Manual download? | Repo destination | How to introduce |
|---|---|---|---|---|---|---|
| IATA-Cargo/ONE-Record GitHub repo | P0 | now | `git clone` or GitHub ZIP | No, scriptable | `data/raw/one_record_repo/` (selected docs only) | extract README, specs, changelog, examples into `.md/.yaml/.jsonld` |
| ONE Record online spec: `development` | P0 | now | save page / scripted scrape to Markdown | Usually yes | `data/raw/one_record_docs/spec_development/` | convert HTML to `.md`, add sidecar metadata |
| ONE Record online spec: `2025-07` | P0 | now | save page / scripted scrape to Markdown | Usually yes | `data/raw/one_record_docs/spec_2025_07/` | convert HTML to `.md`, add sidecar metadata |
| ONE Record online spec: `2023-12` | P1 | after D0 | save page / scripted scrape to Markdown | Usually yes | `data/raw/one_record_docs/spec_2023_12/` | convert HTML to `.md`, add sidecar metadata |
| Official ontology files: TTL / RDF / JSON-LD | P0 | now | from official repo or site | No if in repo, otherwise manual | `data/raw/ontology/official/` | keep originals, add sidecar metadata |
| OpenAPI spec: YAML / JSON | P0 | now | repo or developer portal export | Often manual | `data/raw/api_specs/official/` | store original files, add sidecar metadata |
| JSON-LD examples: Shipment / Waybill / Piece / Notification / Subscription | P0/P1 | now | repo examples or docs examples | Mixed | `data/raw/examples/official/` | store original `.jsonld` plus short explanatory `.md` |
| NE:ONE repo / docs / examples | P0 | immediately after D0 | Git clone + doc extraction | Mixed | `data/raw/ne_one/` | extract README/docs/config/examples into `.md/.txt/.json` |

### D1 — Business and narrative support

| Source | Priority | When | How to obtain | Manual download? | Repo destination | How to introduce |
|---|---|---|---|---|---|---|
| IATA overview page | P0 | after D0 | save page to Markdown | Usually yes | `data/raw/one_record_docs/overview/` | convert to `.md` |
| IATA presentation PDFs / technical insight PDFs | P1 | after D0 | download PDFs, convert to text/Markdown | Yes | `data/raw/one_record_docs/pdfs/` | keep PDF outside ingest if needed; ingest converted `.md/.txt` |
| Air cargo glossary | P1 | after D0 | curate manually from public sources | Yes | `data/raw/notes/domain_glossary/` | author `.md` or `.txt` notes |
| Hackathon / pilot / tutorial examples | P1 | after D1 | collect from public repos/pages | Mostly yes | `data/raw/examples/community/` | store examples and short context notes |
| `awesome-one-record` resource list | P1 | after D1 | clone or copy README | No | `data/raw/notes/community_resources/` | ingest curated summary `.md` |

### D2 — Later expansion

| Source | Priority | When | How to obtain | Manual download? | Repo destination | How to introduce |
|---|---|---|---|---|---|---|
| Cargo-XML / Cargo-IMP comparison material | P2 | later | manual collection | Yes | `data/raw/domain_background/cargo_xml/` | summary notes first, not raw dumps |
| Company / ecosystem materials: Lufthansa / Fraport / DHL / CHAMP / DAKOSY | P2 | later | manual collection | Yes | `data/raw/domain_background/industry/` | summary notes first |

## 4. Manual Download Checklist

These should be treated as manual tasks unless we later build dedicated
downloaders:

- online spec pages from `iata-cargo.github.io`
- IATA overview pages
- IATA presentation PDFs / technical insight PDFs
- OpenAPI files from the developer portal if they are not directly linked in the repo
- hackathon / pilot / tutorial materials
- business glossary curation
- industry ecosystem materials

These are good candidates for you to download manually and place into a staging
folder first:

```text
data/raw/_staging/
```

Then we normalize them into ingestible files under the final folders.

## 5. Recommended Repo Layout

The current project already uses:

```text
data/raw/
├── ontology/
├── one_record_docs/
├── api_specs/
├── examples/
└── notes/
```

To scale that without breaking the loader, use subfolders:

```text
data/raw/
├── ontology/
│   ├── illustrative/
│   └── official/
├── one_record_docs/
│   ├── overview/
│   ├── spec_development/
│   ├── spec_2025_07/
│   ├── spec_2023_12/
│   ├── pdfs/
│   └── ne_one/
├── api_specs/
│   ├── official/
│   └── ne_one/
├── examples/
│   ├── official/
│   ├── community/
│   └── ne_one/
└── notes/
    ├── domain_glossary/
    ├── community_resources/
    └── implementation_notes/
```

## 6. What "Basically Meets Requirements" Means

RecordChat should not claim a serious ONE Record knowledge base until at least
these are present:

1. official ONE Record repo materials
2. official `development` and `2025-07` spec docs
3. official ontology files beyond the current illustrative subset
4. official OpenAPI files
5. a broader JSON-LD example set
6. NE:ONE implementation materials

That is the minimum bar defined by the current source planning scope.

## 7. Import Strategy

Use these ingestion rules:

- standards/spec pages:
  convert HTML/PDF to Markdown, preserve source URL/version in sidecar metadata
- ontology files:
  keep raw files and parse directly
- OpenAPI files:
  ingest raw YAML/JSON and let the API chunker split by endpoint
- JSON-LD examples:
  ingest raw payloads and optionally add explanatory Markdown notes beside them
- NE:ONE source code:
  do not ingest the entire codebase; extract README, docs, configs, sample
  payloads, tests, troubleshooting notes

## 8. Suggested Near-Term Tasks

### First

- manually download or clone the P0 source pack
- place raw assets into `data/raw/_staging/`
- normalize into ingestible file formats and final folders

### Then

- update sidecar metadata for each source batch
- rerun `/ingest`
- extend eval questions so new sources are actually exercised

### Then

- proceed with NE:ONE implementation knowledge
- proceed with ALH and RecordForge only after the knowledge base is broad enough
