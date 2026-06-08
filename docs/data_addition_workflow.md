# Data Addition Workflow

This is the canonical SOP for adding new data to RecordChat.

Use it whenever you add a new source batch, whether the source is official,
community, or implementation-oriented.

Related documents:

- [docs/data_source_plan.md](data_source_plan.md)
- [docs/data_download_guide.md](data_download_guide.md)
- [docs/data_sources_registry.yaml](data_sources_registry.yaml)

## Goal

Every added source batch should follow the same lifecycle:

1. raw intake into `_staging`
2. normalization into final folders
3. provenance registration
4. governance verification
5. ingest refresh
6. optional eval refresh

That keeps the live corpus curated, traceable, and repeatable.

## Standard Flow

### 1. Intake raw files

Put raw downloaded or cloned material under:

```text
data/raw/_staging/
```

Rules:

- keep original filenames if practical
- do not treat `_staging` as ingestable corpus
- do not point loader or custom ingest jobs at `_staging`

### 2. Normalize into ingestable formats

Convert or extract material into loader-friendly formats:

- `.md`
- `.markdown`
- `.txt`
- `.json`
- `.jsonld`
- `.ttl`
- `.owl`
- `.yaml`
- `.yml`

Typical transformations:

- HTML -> Markdown
- PDF -> Markdown or text
- codebase -> selected README/docs/examples/config/test fixtures only

### 3. Place files in final folders

Move normalized files into the correct final destinations under `data/raw/`.

Examples:

- `data/raw/ontology/official/`
- `data/raw/api_specs/official/`
- `data/raw/examples/official/`
- `data/raw/one_record_docs/ne_one/`
- `data/raw/api_specs/ne_one/`
- `data/raw/examples/ne_one/`

### 4. Update source registry

Record the source family and batch in:

- [docs/data_sources_registry.yaml](data_sources_registry.yaml)

For a new batch, add:

- `batch_id`
- `source_path`
- `final_destination`
- `material_types`
- `normalization`
- `license_basis`

### 5. Add or update sidecar metadata

Governed files should carry a sidecar:

```text
<filename>.<ext>.meta.json
```

At minimum, sidecars in governed folders should include:

- `source_name`
- `version`
- `url`
- `document_type`
- `domain`
- `registry_id`
- `batch_id`
- `ingested_at`

### 6. Run the standardized workflow command

After a batch is normalized and registered, run:

```bash
python3 scripts/run_data_addition_workflow.py
```

This will:

1. verify source governance
2. stop if provenance or `_staging` protections are broken
3. print the next recommended ingest step

If you want to immediately rebuild the live corpus too:

```bash
python3 scripts/run_data_addition_workflow.py --ingest
```

If you want a full rebuild:

```bash
python3 scripts/run_data_addition_workflow.py --ingest --reset
```

## Completion Definition

A source batch is considered added correctly when all of these are true:

- raw intake lives in `_staging` only
- normalized files live in final `data/raw` folders
- registry entry exists for the source family and batch
- governed files have matching sidecars
- `python3 scripts/verify_source_governance.py` passes
- if the batch should be live immediately, ingest has been rerun

## Current Automation Boundary

The current automation fully checks the curated core corpus, especially:

- `data/raw/ontology/official/`
- `data/raw/api_specs/official/`
- `data/raw/one_record_docs/ne_one/`
- `data/raw/examples/official/one_record_repo_examples/`
- `data/raw/examples/ne_one/`

Other folders may still rely on lighter manual review until their governance
coverage is expanded.
