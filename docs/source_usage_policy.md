# Source Usage Policy

Last reviewed: 2026-06-07

RecordChat is a citation-first RAG project built on reviewed public materials.
This page is the short external statement of how the project uses third-party
source content.

## Project Position

- RecordChat is a personal, independent project.
- It is not an official IATA product.
- It is not affiliated with, endorsed by, or maintained by IATA.

## How Source Content Is Used

- public technical standards, ontology files, API specs, examples, and
  implementation docs may be normalized for retrieval and citation
- the project uses retrieval-augmented generation rather than training or
  fine-tuning foundation models on third-party source corpora
- answers are intended to point back to sources rather than replace them

## Operating Boundaries

- keep source provenance, version, and URL information wherever practical
- prefer citation-first use over full-content republication
- do not ingest paywalled, login-gated, or access-restricted materials
- do not claim official affiliation with source publishers
- avoid collecting or publishing personal data
- review mixed-license or unclear-license web captures before any public data release

## Practical Implications

- `data/raw/_staging/` is an internal download and normalization workspace
- normalized ingest should come from the final `data/raw` folders
- CI checks are intended to catch regressions where curated ingestable material
  loses provenance metadata or `_staging` protections
- raw third-party source bundles are not intended to be publicly redistributed
- source governance records live in:
  - [docs/data_compliance_report.md](docs/data_compliance_report.md)
  - [docs/data_sources_registry.yaml](docs/data_sources_registry.yaml)

## Related Documents

- [docs/data_compliance_report.md](docs/data_compliance_report.md)
- [docs/data_sources_registry.yaml](docs/data_sources_registry.yaml)
- [docs/data_source_plan.md](docs/data_source_plan.md)
