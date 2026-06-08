# Data Compliance Report

Last reviewed: 2026-06-07

This report reviews the current RecordChat data corpus against the compliance
principles captured in [合规问题.md](</root/Workspace/Recordchat/合规问题.md>).
It is a project governance note, not formal legal advice.

## Executive Summary

Current status: **conditionally acceptable for a citation-first RAG project**.

I did **not** find a clear hard blocker that makes the current dataset obviously
unlawful to keep using for RecordChat's current purpose, because the project is
already operating inside several good boundaries:

- it is positioned as a personal, independent project, not an official IATA tool
- the system is built as RAG over source documents, not as third-party-content
  model training
- `_staging` is now excluded from ingestion by default
- the entire `data/` directory is gitignored, so raw source bundles are not
  being redistributed through this repository by default
- the core official ONE Record repo and the downloaded OpenAPI specs expose
  explicit permissive license signals

That said, the dataset is **not yet fully compliance-hardened**. The biggest
remaining gaps are governance gaps rather than obvious infringement:

- most imported source families now follow a governance pattern, but coverage is
  still incomplete outside the curated core
- several manually downloaded HTML/PDF/web captures rely on source URL records
  rather than per-file license notes
- some staged community and portal pages include third-party site terms or
  copyright notices, so they should remain citation-oriented and not be treated
  as freely redistributable source packs

## Review Scope

Reviewed areas:

- current compliance principles in [合规问题.md](</root/Workspace/Recordchat/合规问题.md>)
- current data layout under `data/raw` and `data/raw/_staging`
- source provenance records such as `SOURCE_URLS.md`
- license signals inside the staged official and community materials
- repository publication posture in [.gitignore](/root/Workspace/Recordchat/.gitignore)

## Findings

### 1. Current project posture is broadly aligned with the intended compliance boundary

The current repo setup already supports a relatively safe operating model:

- `data/` is ignored in Git via [.gitignore](/root/Workspace/Recordchat/.gitignore),
  which reduces accidental redistribution risk
- RecordChat is framed in [README.md](/root/Workspace/Recordchat/README.md) as
  an independent project using public reference materials
- ingestion is now focused on normalized final folders, and `_staging` is not
  part of the live ingest surface
- core governed folders now use registry-linked sidecars and automated checks to
  reduce provenance drift

This matches the recommended boundary from `合规问题.md`: use public materials
for retrieval and citation, avoid republishing full content bundles, and avoid
turning raw downloaded corpora into public redistributable artifacts.

### 2. Core official ONE Record and NE:ONE sources show usable license signals

I found explicit license evidence for the most important technical source sets:

- [data/raw/_staging/ONE-Record/LICENSE](/root/Workspace/Recordchat/data/raw/_staging/ONE-Record/LICENSE)
  is MIT
- [data/raw/_staging/ne_one_implementation_materials/gitlab_repo/LICENSE](/root/Workspace/Recordchat/data/raw/_staging/ne_one_implementation_materials/gitlab_repo/LICENSE)
  is Open Logistics Foundation License 1.3
- [data/raw/_staging/iata_developer_portal_openapi_api_docs/reference_specs/ONE-Record-API-OpenAPI.working_draft.yaml](/root/Workspace/Recordchat/data/raw/_staging/iata_developer_portal_openapi_api_docs/reference_specs/ONE-Record-API-OpenAPI.working_draft.yaml:13)
  declares MIT in the OpenAPI metadata

These are the most important sources for the current product scope, so this is
a meaningful positive signal.

### 3. No major GDPR-style personal-data issue is visible in the current corpus

The current corpus is mainly:

- standards and ontology files
- OpenAPI specs
- JSON-LD examples
- implementation docs/config/examples
- business and community narrative materials

I did not see evidence that the current curated final corpus is centered on
personal data. There are a few public contact fields in source documents, such
as the IATA contact email in the OpenAPI metadata, but this does not look like a
systematic personal-data dataset.

Conclusion: **no obvious current GDPR blocker**, assuming RecordChat continues to
avoid collecting user-uploaded personal data and avoids importing contact lists,
member directories, or operational shipment records tied to natural persons.

### 4. The main current risk is copyright and terms uncertainty in manually captured web/PDF material

Some staged assets clearly point to website terms or copyright notices:

- IATA portal and overview captures contain links to IATA terms pages
- Devpost pages in community materials include site copyright and terms notices
- some ontology HTML mirrors include placeholder or incomplete license markers

This does **not** mean the project is currently non-compliant. It does mean:

- these materials should be used as citation-first reference inputs
- they should not be assumed to be freely redistributable in bulk
- any future public packaging of raw captures should be reviewed source by source

### 5. Source-governance coverage is still too thin

The project now has a source registry plus sidecar metadata across the curated
core, but provenance coverage is still uneven outside that governed set. Some
provenance is still tracked mainly at folder level through `SOURCE_URLS.md` in staging.

This is a meaningful improvement over an ad hoc corpus, but it is still not the
final state for every source family. The project should keep expanding the
registry-plus-sidecar pattern with fields such as:

- `source_url`
- `publisher`
- `license`
- `access_date`
- `version`
- `document_type`
- `allowed_use`
- `restrictions`

## Risk Assessment

### Low risk

- official ONE Record repo material with explicit open license
- OpenAPI spec files that declare MIT
- NE:ONE repo/docs/examples covered by the project license
- ontology TTL/OWL/JSON-LD files used for parsing and retrieval

### Medium risk

- manually downloaded IATA HTML/PDF pages without per-file license notes
- community narrative pages and hackathon captures
- third-party website snapshots kept in `_staging`

### High risk if the project changes behavior

These are not current blockers, but they would become serious problems:

- publishing the raw downloaded corpus as a public redistributable archive
- indexing paywalled, login-gated, or member-only material
- collecting personal data or operational records tied to identifiable people
- training or fine-tuning a model directly on third-party content without a
  clear rights basis
- branding the product as official IATA output

## Conclusion

**Current answer:** there is **no obvious major legal/compliance defect** in the
present RecordChat dataset for its current citation-first RAG use case.

But the project is only **conditionally compliant**, not yet fully hardened.
The remaining work is mostly governance work:

1. keep extending source metadata sidecars and the source registry to imported batches
2. keep `_staging` as internal download workspace only
3. avoid republishing raw third-party web/PDF captures
4. keep final ingestion focused on license-understood, public, non-personal,
   citation-friendly materials

## Recommended Next Actions

1. Keep expanding registry-linked sidecars to remaining governed source families.
2. Keep example-set governance in place as those directories evolve.
3. Keep `_staging` protections under automated verification.
4. Keep community web captures and PDFs out of any future public data release
   unless each source is separately cleared.
