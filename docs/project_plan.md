# RecordChat Project Plan

**Status date:** 2026-09-11
**Current delivered line:** v0.2.6 ALH narrative + RecordForge + Retrieval Quality
**Current next work:** v0.3 sketch only (not scheduled) — see [v03_sketch.md](v03_sketch.md).

> **Agent handoff (2026-09-11).** v0.2.6 ALH (`#7`–`#10`) is **done** on
> `feat/v0.2.6-alh-narrative` (merge when ready). Do not re-open closed
> slices unless a regression appears. **Next scheduled coding is not
> opened** — read [v03_sketch.md](v03_sketch.md) only if the user asks for
> platform work. AUD-08…AUD-10 remain optional P2. Do not start Server
> persist. How to work: [agent_execution_playbook.md](agent_execution_playbook.md).

This is the **current** project plan. Use it when documents disagree.

| Question | Canonical doc |
|---|---|
| Where are we, and what is next? | this file |
| How to execute a slice | [agent_execution_playbook.md](agent_execution_playbook.md) |
| ALH slice brief (done — reference) | [alh_execution_brief.md](alh_execution_brief.md) |
| Milestone narrative | [roadmap.md](roadmap.md) |
| v0.2 task breakdown | [v0.2_development_plan.md](v0.2_development_plan.md) |
| v0.1 API / module contract | [../SPEC.md](../SPEC.md) |
| Knowledge-base import | [data_source_plan.md](data_source_plan.md) |
| Architecture | [architecture.md](architecture.md) |
| Unscheduled platform | [v03_sketch.md](v03_sketch.md) |

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

Frozen product choices (do not reverse without an explicit product decision):

- Synthetic generation **displays** JSON-LD or a workflow result. It does not
  auto-write objects into a ONE Record Server.
- Chat toolbar: **Local JSON-LD** (templates, default) vs **RecordForge**
  (connector workflow).

---

## 2. Milestone board

| Milestone | Status | GitHub |
|---|---|---|
| v0.1 baseline RAG assistant | **done** | SPEC acceptance |
| Data Foundation (core pack) | **mostly done**; `#23` still open | `#21` `#22` `#24` closed; `#23` open |
| v0.2.1 ontology-aware retrieval | **done** | milestone closed; `#1`–`#6` `#26` |
| v0.2.2 NE:ONE implementation Q&A | **done** (baseline) | `#24` `#25` |
| v0.2.3 streaming frontend | **done** | milestone closed; `#15`–`#20` |
| **2026-09 audit P0** (AUD-01…04) | **done** (frontend `/models` wiring deferred) | see §4.7 |
| **Retrieval Quality** | **done** (`#27`–`#31`) | `#27`–`#31` |
| v0.2.4 workflow orchestration | **done** (`#11` `#12` `#32`) | structured workflow_result + connector path |
| v0.2.5 RecordForge | **done** | `#13` `#14` |
| v0.2.6 AviationLakehouse narrative | **done** | `#7`–`#10`; see [alh_execution_brief.md](alh_execution_brief.md) |
| v0.3 platform | **sketch only** | no issues yet |

---

## 3. Execution order (current)

```text
v0.1  ──► Data Foundation  ──► v0.2.1  ──► v0.2.2  ──► v0.2.3
                                               │
                                               ▼
                              2026-09 audit P0 fixes   ✅
                              (AUD-01…AUD-04)
                                               │
                                               ▼
                                    Retrieval Quality ✅
                                    (#27–#31)
                                               │
                                               ▼
                                    finish v0.2.4 (#32) ✅
                                               │
                                               ▼
                                    v0.2.5 RecordForge (#13 #14) ✅
                                               │
                                               ▼
                                    v0.2.6 ALH narrative (#7–#10) ✅
                                               │
                                               ▼
                                    v0.3 platform (auth, memory,
                                    source versioning, tracing)
                                    ◄── sketch only; not scheduled
```

AUD-01…AUD-07, `#27`–`#32`, RecordForge `#13` `#14`, and ALH `#7`–`#10` are
landed. Remaining P2 audit items: AUD-08…AUD-10. No coding slice is scheduled
after ALH until the user opens v0.3.

---

## 4. Retrieval Quality (done — 2026-09-09)

**Status: done.** The problems below were the pre-fix baseline; they are
recorded so agents understand *why* the slice existed. Do not treat this
section as open work.

~~Ontology-aware rerank already exists. That is not the same as “retrieval is
good enough.”~~ Historical issue list (fixed): overlapping ontology /
OpenAPI / spec versions; keyword-only eval; dense-only search; no follow-up
entity carry-over; missing versioned `data/eval/questions.yaml`.

### Goal

Make retrieval **measurable, de-duplicated, and query-type-aware** before
adding more execution features. The 2026-09 audit items (§4.7) are the concrete
first steps of this goal.

### Work

| Step | Issue | Outcome |
|---|---|---|
| 4.1 | [#27](https://github.com/Jiahong-Que-9527/Recordchat/issues/27) | Pin one canonical version per source family (recommended ontology: 2025-07; one OpenAPI; keep `development` + `2025-07` specs). Exclude duplicate TTL / YAML / markdown from ingest and from `OntologyGraph`. Context: AUD-02. |
| 4.2 | [#28](https://github.com/Jiahong-Que-9527/Recordchat/issues/28) | Gold-chunk eval: recall@5, MRR, source-family / version accuracy. Requires the eval set restored first (AUD-01). |
| 4.3 | [#29](https://github.com/Jiahong-Que-9527/Recordchat/issues/29) | Hybrid / lexical candidates + metadata filters by query type. |
| 4.4 | [#30](https://github.com/Jiahong-Que-9527/Recordchat/issues/30) | Follow-up questions keep entities (history + rewrite). Context: AUD-06. |
| 4.5 | [#31](https://github.com/Jiahong-Que-9527/Recordchat/issues/31) | `sources` lists chunks that support the answer. Context: AUD-05. |

### Acceptance

- [x] A given class/property has one live canonical chunk (plus glossary), not 4–6 near-duplicates
- [x] Eval can fail because the wrong source family or ontology version ranked first
- [x] NE:ONE setup/config questions cite docs/config, not bulk example JSON
- [x] “What is a Piece?” → “how does it relate to Shipment?” still retrieves both entities
- [x] `data/eval/questions.yaml` exists, is committed, and `evaluate_rag.py` loads it (AUD-01)
- [x] `/chat` field names stay stable

### 4.8 Agent notes for the closed slice

- Canonical allowlists live in `Settings` (`canonical_*_versions`) and
  `rag/canonical.py`.
- Hybrid search: dense Qdrant + in-process BM25 (`rag/lexical.py`) fused with RRF.
- Synthetic intents **skip RAG** and call `connectors.orchestration.run_synthetic_data_workflow`.
- Request diagnostics: `RECORDCHAT_REQUEST_LOG` → stdout (default) or a JSONL path.

Suggested order inside the slice: **AUD-01 → #27 (with AUD-02) → #28 → #29 →
#30 / #31**, with AUD-03 / AUD-04 done as one-shot fixes before or alongside.
Eval (#28) should land early so later retrieval changes have a regression gate.

### 4.7 2026-09 audit findings (AUD-01…AUD-10)

Findings from the 2026-09-08 code review. Each item lists the evidence and the
agreed fix. Priority: P0 = do now (blocks trustworthy retrieval), P1 = this
slice, P2 = next slice. **Agents must check this table before starting work —
some of these invalidate assumptions in older docs.**

| ID | Priority | Finding (evidence) | Fix / direction |
|---|---|---|---|
| AUD-01 | **P0** | `data/eval/questions.yaml` does not exist and was **never committed** (git history has no copy; `data/` is fully gitignored). `scripts/evaluate_rag.py:36` hard-reads it → eval crashes. SPEC Phase 9 “≥10 questions” is effectively under-delivered. | Restore a ≥10-question eval set; **exempt `data/eval/` from the `data/` gitignore** so the set is versioned (it is our own authored content, no third-party rights). Update `evaluate_rag.py` to fail with a clear message when the file is absent. |
| AUD-02 | **P0** | Canonical-version duplication is broader than ontology: `ontology/official/` has 2023-12 + 2025-07 + working_draft + `api_ontology.current` (TTL/OWL/JSON-LD each); `api_specs/official/` has 3 OpenAPI versions; `one_record_docs/` nests 3 spec versions live at once. One class/property yields 4+ chunks. | Introduce a **canonical source version policy** (see `docs/data_source_plan.md` §10): config-driven `source family → canonical version` mapping; `loader.py` skips non-canonical versions; extend `verify_source_governance.py` with a duplicate-chunk report. |
| AUD-03 | **P0** | `reranker.py` score = `(len - index) + boost`; boosts (10/12) exceed the max possible rank gap (1), so **entity boosts fully override vector similarity**. Any `detect_entities` false positive drags an unrelated ontology chunk to position 1. | Re-weight: keep vector rank dominant (e.g. multiplicative or much smaller additive boosts); add a regression test asserting non-entity queries preserve vector order and entity boost cannot reorder unrelated chunks to rank 1. |
| AUD-04 | **P0** | Default-drift between docs and runtime: `SPEC.md` §8 / README still present `qwen`/`qwen-plus` as the default provider/model, while `config.py`, `.env.example`, and `docker-compose.yml` all default to `openai` + `kimi-k3` (flash). The frontend `CHAT_MODELS` allowlist and `ModelPicker` labels do match the backend `llm.py` Literal (flash + pro), but the list is hardcoded in three places, so any backend change silently breaks the picker. | Reconcile the docs with the runtime defaults (or vice versa); expose the model allowlist from the backend (e.g. `GET /models`) so the frontend picker derives from the same source and cannot drift. |
| AUD-05 | P1 | `sources` returns the full retrieved candidate list, not just chunks that actually support the answer (citation noise; fails “prefer no citation over a wrong citation”). | `#31`: prompt requires per-source references; backend filters `sources` to cited chunks. |
| AUD-06 | P1 | Multi-turn context is lost: frontend `useChat` has history but only sends `model`; backend retrieves on the bare follow-up sentence (“how does it relate to Shipment?” loses “Piece”). | `#30`: send `conversation_id` + history from frontend; backend does query rewrite / entity carry-over before retrieval (keep it inside `pipeline.py`). |
| AUD-07 | P1 ✅ | No diagnostic evidence capture: `answer()` logs nothing structured (query, query_type, retrieved chunks/rank, latency, errors). Blocks §4.6 expert-interview evidence and `#31` debugging. | **Done:** `app/core/request_log.py` + `RECORDCHAT_REQUEST_LOG` (stdout / file / off). |
| AUD-08 | P2 | `answer()` and `answer_stream()` duplicate ~60% of orchestration; `_is_ontology_query()` is defined twice (pipeline + reranker) with **different** rule sets (reranker copy lacks the Chinese markers). | Extract shared helpers into one module; single source for `_is_ontology_query`. Refactor only — no behavior change beyond AUD-03. |
| AUD-09 | P2 | Infra pinning: `docker-compose.yml` uses `qdrant:latest`; Qdrant unauthenticated (acceptable local, must be resolved before any public deployment); backend default `llm_model` is incoherent (see AUD-04). | Pin qdrant image version; document auth posture; revisit before any hosted deployment. |
| AUD-10 | P2 | Eval is not in CI (needs real API keys). Risk: retrieval regressions (e.g. `#27`/`#29`) land unnoticed. | Add a **CI-safe retrieval regression test** using a fake embedding provider over a tiny fixture corpus with gold chunks — asserts recall and canonical-version ranking without network. |

Execution note for agents: AUD-01 and AUD-02 are prerequisites for `#28` and
`#27` respectively; AUD-03 and AUD-04 are small, independent, and can be
delivered immediately. AUD-07 should land before the §4.6 expert interviews so
sessions produce captureable evidence.

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
  version, latency, and any error for every tested turn. Depends on AUD-07
  (request logging), which must land before the interviews start.
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

### v0.2.4 Workflow — done

[#32](https://github.com/Jiahong-Que-9527/Recordchat/issues/32): structured
`workflow_result` in `structured_output`, RecordForge connector execution path
(plan + request artifact), decoupled from RAG retrieval. Live HTTP landed in `#13`.

### v0.2.5 RecordForge — **done**

[#13](https://github.com/Jiahong-Que-9527/Recordchat/issues/13),
[#14](https://github.com/Jiahong-Que-9527/Recordchat/issues/14).

Landed:

- `#13`: `RecordForgeConnector` POSTs to `{RECORDFORGE_URL}/v1/generate` when
  configured; transport / HTTP errors → `unavailable` + `failed` workflow
- unconfigured → `status=blocked` (unchanged)
- `#14`: frontend `WorkflowViewer` renders status / steps / artifacts; Canvas
  no longer treats workflow results as JSON-LD
- UI toggle `synthetic_mode`: **Local JSON-LD** (default, templates) vs
  **RecordForge** (workflow). Generation **displays** in the panel; it does
  not write to a ONE Record Server.

Backend tests cover ready / unconfigured / unavailable / local templates.

### v0.2.6 AviationLakehouse — **done**

[#7](https://github.com/Jiahong-Que-9527/Recordchat/issues/7)–[#10](https://github.com/Jiahong-Que-9527/Recordchat/issues/10).

Landed (see [alh_execution_brief.md](alh_execution_brief.md)):

- `#7` `data/raw/one_record_docs/aviation_lakehouse.md` + sidecar
- `#8` `domain/alh_mapping.py` (Bronze/Silver/Gold helpers)
- `#9` additive `QueryType.architecture_question` + prompt/glossary hooks
- `#10` three eval questions + demo prompts

Narrative only: no live lakehouse, no Server persist.

### Data Foundation leftover

[#23](https://github.com/Jiahong-Que-9527/Recordchat/issues/23) (IATA overview /
PDFs / community pages) is **not** a blocker for Retrieval Quality. Do not bulk
ingest more community HTML/PDF until #27 and #28 are done.

---

## 6. v0.3 sketch (not scheduled)

See [v03_sketch.md](v03_sketch.md) for the ordered sketch (auth, memory,
source admin, tracing, eval dashboard, optional live Server/ALH connectors).

No GitHub issues yet. Do not pull these into v0.2. Product freeze: synthetic
objects are shown in the UI; auto-persist to a ONE Record Server is **not**
current work.

---

## 7. Not now

- claiming official IATA affiliation
- fine-tuning on third-party ONE Record text
- ingesting `_staging/` or republishing raw upstream bundles
- replacing the retriever ABC with a framework-specific chain
- letting the LLM emit JSON-LD structure (templates stay in `domain/`)
- ALH / RecordForge work that skips Retrieval Quality
- heavy tracing / auth / eval dashboard — these stay in the §6 v0.3 sketch (see AUD-07 for the lightweight logging that *is* in scope)

---

## 8. Definition of done for the current iteration

The current iteration (2026-09 audit P0 + Retrieval Quality) is done when:

- [x] **AUD-01** — `data/eval/questions.yaml` exists (≥10 questions), is
      committed (gitignored-exempt), and `evaluate_rag.py` runs without
      crashing.
- [x] **AUD-02** — one live canonical version per source family (ontology +
      OpenAPI + spec docs); `verify_source_governance.py` reports no live
      duplicates; a class/property yields one canonical chunk (+glossary).
- [x] **AUD-03** — reranker no longer lets entity boosts override vector rank;
      non-entity queries keep vector order (covered by a regression test).
- [x] **AUD-04** — runtime defaults coherent with docs; backend exposes
      `GET /models` as the allowlist source of truth. Frontend picker still
      hardcodes the same list (UI wiring deferred by choice).
- [x] `#27`–`#31` meet their issue acceptance criteria (§4), and
      `scripts/evaluate_rag.py` reports retrieval metrics (recall@5 / MRR /
      source-family accuracy) that can go red.
- [x] Backend tests green, `verify_source_governance.py` green.
      (Visual UI unchanged; BFF `app/api/chat/route.ts` now forwards history.)
- [x] **#32** — structured `workflow_result` + connector execution path
      (live HTTP deferred to `#13`).
- [x] **AUD-07** — lightweight request JSONL / stdout diagnostics.

**This iteration is closed.** RecordForge `#13` `#14` is also closed (see
AGENTS.md §7). Next DoD is ALH `#7`–`#10` —
[alh_execution_brief.md](alh_execution_brief.md) §7.
