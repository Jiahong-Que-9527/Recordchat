# RecordChat Data Download Guide

This is the operational companion to:

- [docs/data_source_plan.md](data_source_plan.md)
- [dl数据下载清单.md](../dl数据下载清单.md)

Use this guide when you actually start collecting files.

## 1. Working Rule

Follow this workflow for every batch:

1. download raw files into `data/raw/_staging/`
2. keep original filenames if possible
3. convert non-ingestible files to `.md` / `.txt` / `.jsonld` / `.yaml`
4. move normalized files into their final folders
5. add sidecar metadata if the source is important enough to cite precisely

## 2. What Counts As Ingestible Right Now

The current loader reads:

- `.ttl`
- `.owl`
- `.md`
- `.markdown`
- `.txt`
- `.json`
- `.jsonld`
- `.yaml`
- `.yml`

That means:

- HTML pages should be saved or converted to Markdown
- PDFs should be converted to Markdown or plain text
- raw images/diagrams should not be ingested directly
- source code should not be bulk-ingested; extract README/docs/examples/configs/tests

## 3. Download Queue

### A. Official ONE Record repo

**Download from**

- GitHub repo:
  https://github.com/IATA-Cargo/ONE-Record
- Releases page:
  https://github.com/IATA-Cargo/ONE-Record/releases

**What to take**

- `working_draft/` or equivalent latest documentation area
- release folders such as `2025-07/` and `2023-12/`
- ontology files
- API/security specification materials
- changelog / release notes
- example payloads if present

**How to get it**

- preferred: clone the repo or download ZIP
- then extract only the useful docs/spec/example files into `data/raw`

**Place into**

- repo-derived docs:
  `data/raw/one_record_docs/spec_development/`
  `data/raw/one_record_docs/spec_2025_07/`
  `data/raw/one_record_docs/spec_2023_12/`
- ontology files:
  `data/raw/ontology/official/`
- examples:
  `data/raw/examples/official/`
- changelog / notes:
  `data/raw/notes/implementation_notes/`

**Manual?**

- mostly scriptable
- no manual download required unless you prefer ZIP over clone

### B. Official online specification pages

**Download from**

- development docs:
  https://iata-cargo.github.io/ONE-Record/development/
- stable docs landing:
  https://iata-cargo.github.io/ONE-Record/stable/General/Getting-Started-with-ONE-Record/
- `2025-07` docs:
  https://iata-cargo.github.io/ONE-Record/2025-07/
- `2023-12` docs:
  https://iata-cargo.github.io/ONE-Record/2023-12/

**What to take**

- general introduction pages
- data model pages
- API/security pages
- implementation guideline pages
- logistics object pages
- subscription/notification pages

**How to get it**

- manual save as HTML, then convert to Markdown
- or use a page-to-Markdown tool yourself

**Place into**

- development version:
  `data/raw/one_record_docs/spec_development/`
- `2025-07`:
  `data/raw/one_record_docs/spec_2025_07/`
- `2023-12`:
  `data/raw/one_record_docs/spec_2023_12/`

**Manual?**

- yes, treat this as manual download + normalization work

### C. IATA overview and business-facing materials

**Download from**

- overview page:
  https://www.iata.org/one-record/
- fact sheet:
  https://www.iata.org/en/iata-repository/pressroom/fact-sheets/fact-sheet-one-record/
- presentation PDF:
  https://www.iata.org/contentassets/a1b5532e38bf4d6284c4bf4760646d4e/iata_one_record_presentation_en.pdf
- data model PDF:
  https://www.iata.org/contentassets/a1b5532e38bf4d6284c4bf4760646d4e/data-insight-the-one-record-data-model-digital-twin-of-the-air-cargo-industry.pdf
- API tech insight PDF:
  https://www.iata.org/contentassets/a1b5532e38bf4d6284c4bf4760646d4e/one_record_tech_insight_api.pdf
- implementation playbook PDF:
  https://www.iata.org/contentassets/a1b5532e38bf4d6284c4bf4760646d4e/iata_one_record_implementationplaybook.pdf
- development dashboard PDF:
  https://www.iata.org/contentassets/a1b5532e38bf4d6284c4bf4760646d4e/iata_one_record_standard_development_dashboard.pdf

**What to take**

- overview page content
- executive summary / benefits / positioning content
- technical insight PDFs
- business-facing or implementation-facing white papers

**How to get it**

- download PDFs manually
- convert them to `.md` or `.txt`
- keep the raw PDFs outside ingest if you want, but ingest only converted text

**Place into**

- overview pages:
  `data/raw/one_record_docs/overview/`
- converted PDF text:
  `data/raw/one_record_docs/pdfs/`

**Manual?**

- yes

### D. Ontology and vocabulary pages

**Download from**

- developer portal landing:
  https://onerecord.iata.org/index.html
- API vocabulary page:
  https://onerecord.iata.org/api/index-en.html
- API ontology documentation mirror:
  https://iata-cargo.github.io/api-ontology/

**What to take**

- vocabulary and ontology documentation pages
- links to ontology serializations if available
- class/property descriptions

**How to get it**

- if serialization files are directly downloadable, keep them as raw ontology files
- if only docs pages are easily accessible, save them as Markdown/text too

**Place into**

- ontology serializations:
  `data/raw/ontology/official/`
- vocabulary documentation pages:
  `data/raw/one_record_docs/overview/`

**Manual?**

- mixed
- often manual unless direct file links are obvious

### E. OpenAPI and API docs

**Download from**

- IATA Developer Portal home:
  https://developer.iata.org/
- ONE Record developer portal landing:
  https://onerecord.iata.org/index.html

**What to take**

- `openapi.yaml`
- `openapi.json`
- endpoint documentation if separate
- auth/security schema if available

**How to get it**

- if you can export/download the OpenAPI files directly, keep them raw
- if the docs are only visible in HTML pages, save additional `.md` notes

**Place into**

- official OpenAPI files:
  `data/raw/api_specs/official/`
- additional API notes:
  `data/raw/notes/implementation_notes/`

**Manual?**

- usually yes
- mark these as manual if the developer portal does not expose stable direct file URLs

### F. Official JSON-LD examples

**Download from**

- examples from the official GitHub repo:
  https://github.com/IATA-Cargo/ONE-Record
- examples referenced in the online specification pages

**What to take**

- Shipment examples
- Waybill examples
- Piece examples
- LogisticsObject examples
- Notification examples
- Subscription examples
- error response examples

**How to get it**

- save raw `.jsonld` or `.json`
- optionally add a companion `.md` note explaining what the payload is

**Place into**

- `data/raw/examples/official/`

**Manual?**

- mixed
- if examples are embedded in docs pages, yes, manual extraction

### G. NE:ONE implementation materials

**Download from**

- NE:ONE project page:
  https://openlogisticsfoundation.org/topics/neone/
- NE:ONE release note:
  https://openlogisticsfoundation.org/neone-open-source-software-released-revolutionising-modern-data-exchange-in-air-freight/
- NE:ONE GitLab repo root:
  https://git.openlogisticsfoundation.org/wg-digitalaircargo/ne-one

**What to take**

- README
- docs
- config files
- Docker/deployment files
- example payloads
- tests that explain usage or failure modes

**How to get it**

- clone the GitLab repo if accessible
- do **not** ingest the whole codebase blindly
- extract docs/examples/config/tests summaries into text-like files

**Place into**

- docs converted to text:
  `data/raw/one_record_docs/ne_one/`
- API/config materials:
  `data/raw/api_specs/ne_one/`
- example payloads:
  `data/raw/examples/ne_one/`
- troubleshooting and extracted notes:
  `data/raw/notes/implementation_notes/`

**Manual?**

- mixed
- repo clone is scriptable, but summarizing usable implementation knowledge is manual/curated

### H. Community and narrative add-ons

**Download from**

- `awesome-one-record` or your curated equivalent
- hackathon / pilot / tutorial pages
- public ecosystem materials you decide to keep

**What to take**

- resource list README or summary notes
- selected example payloads
- pilot/demo descriptions
- tutorial snippets worth turning into notes

**Place into**

- resource summaries:
  `data/raw/notes/community_resources/`
- payload examples:
  `data/raw/examples/community/`

**Manual?**

- yes

## 4. Sidecar Metadata Template

For important imported files, add:

```json
{
  "source_name": "Human readable source name",
  "version": "development | 2025-07 | 2023-12 | demo | other",
  "url": "https://example.com/original-source",
  "document_type": "ontology | api_spec | docs | example | notes",
  "domain": "one_record",
  "ingested_at": "ISO-8601 timestamp"
}
```

## 5. First Manual Batch To Download

If you want the best next step with the least ambiguity, download these first:

1. official online spec pages for `development` and `2025-07`
2. IATA overview page and the presentation / data model / API PDFs
3. official OpenAPI files if you can export them
4. NE:ONE repo docs/examples/config materials
5. official JSON-LD examples beyond the current single `piece_example`

Put all of that first into:

```text
data/raw/_staging/
```

Then we can normalize and redistribute them into the final folders above.
