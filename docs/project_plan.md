# RecordChat Project Plan

**Status date:** 2026-08-15
**Current delivered line:** v0.2.3 (streaming, source-grounded ONE Record assistant)
**Current next work:** Retrieval Quality (`#27`–`#31`), then finish workflow

This is the **current** project plan. Use it when documents disagree.

| Question | Canonical doc |
|---|---|
| Where are we, and what is next? | this file |
| Milestone narrative | [roadmap.md](roadmap.md) |
| v0.2 task breakdown | [v0.2_development_plan.md](v0.2_development_plan.md) |
| v0.1 API / module contract | [../SPEC.md](../SPEC.md) |
| Knowledge-base import | [data_source_plan.md](data_source_plan.md) |
| Architecture | [architecture.md](architecture.md) |

`SPEC.md` remains the contract for `/chat`, `/ingest`, and module boundaries.
It is **not** the execution-order source after v0.1.

---

## 1. Product

RecordChat is a citation-first RAG assistant for IATA ONE Record (concepts,
ontology, JSON-LD, API, NE:ONE). It is independent of IATA. It retrieves
reviewed public sources; it does not fine-tune on third-party corpora.

Later ecosystem (not this iteration):

```text
RecordChat        = AI interface for ONE Record knowledge
RecordForge       = synthetic ONE Record data generator
ONE Record Server = standardized data exchange layer
AviationLakehouse = analytical backend (Bronze / Silver / Gold, deferred)
```

---

## 2. Milestone board

| Milestone | Status | GitHub |
|---|---|---|
| v0.1 baseline RAG assistant | **done** | SPEC acceptance |
| Data Foundation (core pack) | **mostly done**; `#23` still open | `#21` `#22` `#24` closed; `#23` open |
| v0.2.1 ontology-aware retrieval | **done** | milestone closed; `#1`–`#6` `#26` |
| v0.2.2 NE:ONE implementation Q&A | **done** (baseline) | `#24` `#25` |
| v0.2.3 streaming frontend | **done** | milestone closed; `#15`–`#20` |
| **Retrieval Quality** | **next / in progress** | `#27`–`#31` |
| v0.2.4 workflow orchestration | **partial** (`#11` `#12` done) | remainder `#32`; blocked on retrieval quality |
| v0.2.5 RecordForge | **not started** | `#13` `#14` |
| v0.2.6 AviationLakehouse narrative | **deferred** | `#7`–`#10` |
| v0.3 platform | **sketch only** | no issues yet |

---

## 3. Execution order (current)

```text
v0.1  ──► Data Foundation  ──► v0.2.1  ──► v0.2.2  ──► v0.2.3
                                              │
                                              ▼
                                    Retrieval Quality   ◄── you are here
                                    (#27 ontology pin
                                     #28 gold eval
                                     #29 hybrid + filters
                                     #30 history / rewrite
                                     #31 citation filter)
                                              │
                                              ▼
                                    finish v0.2.4 (#32)
                                              │
                                              ▼
                                    v0.2.5 RecordForge (#13 #14)
                                              │
                                              ▼
                                    v0.2.6 ALH narrative (#7–#10)
                                              │
                                              ▼
                                    v0.3 platform (auth, memory,
                                    source versioning, tracing)
```

Do not start RecordForge or ALH while retrieval still fails open (duplicate
ontology chunks, keyword-only eval, no hybrid, no follow-up context).

---

## 4. Retrieval Quality (the missing slice)

Ontology-aware rerank already exists. That is not the same as “retrieval is
good enough.” The live corpus currently indexes overlapping ontology copies
(2023-12, 2025-07, working draft, spec bundles, NE:ONE copies, community
Checks TTL). Eval treats “any source returned” as a hit. Search is dense-only
with a pool of at most 20. The chat adapter sends only the latest user
sentence.

### Goal

Make retrieval **measurable, de-duplicated, and query-type-aware** before
adding more execution features.

### Work

| Step | Issue | Outcome |
|---|---|---|
| 4.1 | [#27](https://github.com/Jiahong-Que-9527/Recordchat/issues/27) | Pin one canonical ontology (recommended: 2025-07); exclude duplicate TTL from ingest and from `OntologyGraph` |
| 4.2 | [#28](https://github.com/Jiahong-Que-9527/Recordchat/issues/28) | Gold-chunk eval: recall@5, MRR, source-family / version accuracy |
| 4.3 | [#29](https://github.com/Jiahong-Que-9527/Recordchat/issues/29) | Hybrid / lexical candidates + metadata filters by query type |
| 4.4 | [#30](https://github.com/Jiahong-Que-9527/Recordchat/issues/30) | Follow-up questions keep entities (history + rewrite) |
| 4.5 | [#31](https://github.com/Jiahong-Que-9527/Recordchat/issues/31) | `sources` lists chunks that support the answer |

### Acceptance

- [ ] A given class/property has one live canonical chunk (plus glossary), not 4–6 near-duplicates
- [ ] Eval can fail because the wrong source family or ontology version ranked first
- [ ] NE:ONE setup/config questions cite docs/config, not bulk example JSON
- [ ] “What is a Piece?” → “how does it relate to Shipment?” still retrieves both entities
- [ ] `/chat` field names stay stable

Suggested order inside the slice: **#27 → #28 → #29 → #30 / #31**. Eval (#28)
should land early so later retrieval changes have a regression gate.

### 4.6 External expert mini interviews — TODO (parallel, non-blocking)

Run a short formative validation round with **3–5 external IATA ONE Record
practitioners**. This is a discovery activity that can start now; it does not
replace the automated retrieval acceptance criteria above and must not block
`#27`–`#31`.

**Format:** one 10–20 minute session per participant. After a brief product
introduction, ask the expert to enter 2–3 real questions from their work. Keep
two standard fallback questions so results remain comparable. For each answer,
ask whether the conclusion is correct, whether its cited sources support it,
and whether the expert could act on it.

**TODO**

- [ ] **Before interviews — freeze the test environment:** pin the app revision,
  selected model, prompt configuration, corpus, and canonical ontology version;
  run a fresh ingest and record those values in the session log.
- [ ] **Before interviews — run an internal smoke pass:** test 10–15 questions
  spanning concepts, relationships, ontology, API/NE:ONE implementation, and
  JSON-LD; resolve empty answers, broken source links, clearly irrelevant
  citations, and structured-output rendering failures before external sessions.
- [ ] **Before interviews — make evidence inspectable:** ensure each response
  visibly identifies its source name, section, and working link; prefer no
  citation over a citation that does not support the conclusion.
- [ ] **Before interviews — capture diagnostic evidence:** save the question,
  answer, returned source chunks and ranking, model/configuration, corpus
  version, latency, and any error for every tested turn.
- [ ] **Before interviews — add uncertainty guardrails:** where evidence is
  missing, ambiguous, or version-sensitive, have answers state their limits
  rather than presenting an unsupported conclusion as certain.
- [ ] **Before interviews — give lightweight onboarding:** provide a one-screen
  scope prompt (concepts, ontology, JSON-LD, API, and NE:ONE troubleshooting)
  so experts can start with relevant questions without constraining their
  real-world queries.
- [ ] Recruit 3–5 participants spanning ONE Record standard/ontology, business
  implementation, and API/NE:ONE integration perspectives.
- [ ] Prepare a lightweight interview script, consent/recording note if
  applicable, and two standard fallback questions.
- [ ] Capture an expert verdict for each response: correct / partly correct /
  incorrect / cannot assess; also record citation trust and actionability.
- [ ] Tag findings by severity (trust-breaking, core-task blocker, improvement)
  and synthesize the recurring gaps.
- [ ] Convert reviewed questions into a small gold evaluation set with expected
  answer points and acceptable source chunks; feed the retrieval-specific cases
  into `#28` and citation failures into `#31`.

**Success signal:** identify the top expert-valued use cases, the most serious
trust failures, and at least 10 reviewed question-and-source cases suitable for
regression evaluation. Do not treat this small qualitative sample as a product
accuracy claim.

---

## 5. Remaining v0.2

### v0.2.4 Workflow — remainder

[#32](https://github.com/Jiahong-Que-9527/Recordchat/issues/32): structured
workflow results and an execution path behind the Connector ABC. `#11` / `#12`
already provide the seam and synthetic-generation routing.

### v0.2.5 RecordForge

[#13](https://github.com/Jiahong-Que-9527/Recordchat/issues/13),
[#14](https://github.com/Jiahong-Que-9527/Recordchat/issues/14). Optional HTTP
connector; unconfigured deployments must keep degrading as they do today.

### v0.2.6 AviationLakehouse

[#7](https://github.com/Jiahong-Que-9527/Recordchat/issues/7)–[#10](https://github.com/Jiahong-Que-9527/Recordchat/issues/10).
Narrative + domain mapping only after the ONE Record assistant path is strong.

### Data Foundation leftover

[#23](https://github.com/Jiahong-Que-9527/Recordchat/issues/23) (IATA overview /
PDFs / community pages) is **not** a blocker for Retrieval Quality. Do not bulk
ingest more community HTML/PDF until #27 and #28 are done.

---

## 6. v0.3 sketch (not scheduled)

- authentication and persisted sessions
- conversation memory beyond request-scoped rewrite
- source versioning and ingest admin
- OpenTelemetry and an evaluation dashboard
- live connectors: ONE Record Server, RecordForge, AviationLakehouse

No GitHub issues yet. Do not pull these into v0.2.

---

## 7. Not now

- claiming official IATA affiliation
- fine-tuning on third-party ONE Record text
- ingesting `_staging/` or republishing raw upstream bundles
- replacing the retriever ABC with a framework-specific chain
- letting the LLM emit JSON-LD structure (templates stay in `domain/`)
- ALH / RecordForge work that skips Retrieval Quality

---

## 8. Definition of done for the current iteration

Retrieval Quality is done when #27–#31 meet their issue acceptance criteria and
`scripts/evaluate_rag.py` reports retrieval metrics that can go red. After that,
v0.2.4 (#32) is unblocked.
