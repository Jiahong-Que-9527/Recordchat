# `data/raw` layout

This folder now has two layers:

1. the original v0.1 demo files kept in their current locations
2. the expanded source skeleton for official ONE Record, NE:ONE, and manual downloads

Download instructions:

- high-level plan:
  [docs/data_source_plan.md](/root/Workspace/Recordchat/docs/data_source_plan.md)
- direct source links and folder mapping:
  [docs/data_download_guide.md](/root/Workspace/Recordchat/docs/data_download_guide.md)

## Use this flow

- put manually downloaded files into `data/raw/_staging/`
- normalize them into ingestible formats such as `.md`, `.txt`, `.jsonld`, `.yaml`
- move them into the final folders below
- add sidecar metadata files where appropriate

## Final folders

- `ontology/illustrative/`
  current demo or intentionally small ontology subsets
- `ontology/official/`
  official ONE Record ontology files such as `.ttl`, `.owl`, `.rdf`, `.jsonld`
- `one_record_docs/overview/`
  overview pages and general official documentation
- `one_record_docs/spec_development/`
  development-version spec docs converted to Markdown/text
- `one_record_docs/spec_2025_07/`
  current stable spec docs converted to Markdown/text
- `one_record_docs/spec_2023_12/`
  older stable spec docs for comparison
- `one_record_docs/pdfs/`
  PDF-derived Markdown/text, not the raw PDFs themselves
- `one_record_docs/ne_one/`
  NE:ONE documentation excerpts converted to ingestible text
- `api_specs/official/`
  official OpenAPI YAML/JSON
- `api_specs/ne_one/`
  NE:ONE-specific API or config schema material
- `examples/official/`
  official JSON-LD payloads and example objects
- `examples/community/`
  hackathon, pilot, tutorial, or community example payloads
- `examples/ne_one/`
  NE:ONE example payloads and sample requests
- `notes/domain_glossary/`
  manually curated business/domain glossary notes
- `notes/community_resources/`
  curated summaries of ecosystem resources such as `awesome-one-record`
- `notes/implementation_notes/`
  troubleshooting notes, setup notes, and extracted implementation guidance
- `domain_background/cargo_xml/`
  later comparison material for Cargo-XML / Cargo-IMP
- `domain_background/industry/`
  later ecosystem material for airlines, handlers, and cargo platforms

See [docs/data_source_plan.md](/root/Workspace/Recordchat/docs/data_source_plan.md) for the full plan.
