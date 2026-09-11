# Expert session script (external Q&A test)

Facilitator crib for a **10–20 minute** session with one IATA ONE Record
practitioner. This is discovery, not an accuracy claim.

Companion: [demo_cheat_sheet.md](demo_cheat_sheet.md).  
Diagnostics: `RECORDCHAT_REQUEST_LOG` → `data/logs/requests.jsonl`.

## 0. Before the participant arrives (5 min)

```bash
git rev-parse --short HEAD          # freeze revision
make session-env                    # revision + /health
make ingest                         # only if corpus/code changed since last ingest
mkdir -p data/logs
# Recreate backend so Docker picks up the logs mount (first time only):
#   docker compose up -d backend
```

Fill this freeze block (copy into the session notes):

```text
date_utc:
revision:
branch:
llm_model:
embedding_model:
qdrant_collection:
canonical_ontology: 2025-07
request_log: data/logs/requests.jsonl
participant_id: P0_
role:  ontology / business / NE:ONE-API
consent_notes_ok: yes / no
```

Open http://localhost:3000, new chat, model **DeepSeek V4 Flash** unless you
explicitly test Pro. Leave generation mode on **Local JSON-LD** unless the
prompt is a RecordForge workflow demo.

Tail logs in another terminal: `make request-log`.

## 1. One-screen scope (read aloud, ~45 s)

> RecordChat is an independent, citation-first assistant for **IATA ONE Record**.
> It is **not** an official IATA product.
>
> It is strongest on: concepts, ontology, JSON-LD **examples**, API ideas, and
> NE:ONE local setup. Answers should come with sources; if a citation looks
> wrong, treat “no citation” as better than a bad one.
>
> Please treat as **illustrative, not official**:
> - generated JSON-LD (templates)
> - AviationLakehouse Bronze / Silver / Gold (project narrative, no live lake)
>
> Not in this build: login, saved history, writing objects into a ONE Record
> Server, or a live RecordForge unless we say it is configured.
>
> Ask **your real work questions**. If we stall, I have two fallback prompts.

## 2. Flow (10–20 min)

1. Participant asks **2–3 questions from their work** (type, don’t paste huge logs).
2. After **each** answer, ask the three verdict questions below.
3. If they freeze, use **fallback A then B** (same for every participant).
4. Optional third fallback if time remains.

Do not correct the assistant during the session unless it is clearly broken
(blank screen, error banner). Note the issue and continue.

### Three questions after every answer

1. **Conclusion:** correct / partly correct / incorrect / cannot assess  
2. **Citations:** do the listed sources support the conclusion? yes / partial / no / none shown  
3. **Actionable:** could you act on this at work? yes / with caveats / no

Severity tag (optional, you fill after they leave):

- `trust-breaking` — would stop using it
- `core-task blocker` — cannot complete a real task
- `improvement` — annoying but usable

## 3. Fallback prompts (keep these identical across sessions)

**A — concept (always)**  
`What is a Piece in ONE Record?`

**B — ontology (always)**  
`What properties connect Shipment to Piece in the ONE Record ontology?`

**C — optional, if they are an implementer**  
`How do I start NE:ONE locally with docker compose?`

Do **not** lead with ALH, RecordForge, or JSON-LD generation unless they ask.
Those are demo features; expert time is for real questions.

If they *do* ask to generate data: Local JSON-LD is the default. RecordForge
without `RECORDFORGE_URL` will show a **Blocked** workflow — that is expected.

## 4. Score sheet (one row per answer)

Copy per participant:

| # | Question (verbatim) | query_type if visible | Conclusion | Citations | Actionable | Severity | Notes |
|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |
| A | What is a Piece in ONE Record? |  |  |  |  |  |  |
| B | What properties connect Shipment to Piece… |  |  |  |  |  |  |

After the session, match rows to `data/logs/requests.jsonl` by timestamp /
query text. Keep participant names out of the JSONL notes if they did not
consent to being identified.

## 5. After they leave (5 min)

- [ ] Save freeze block + score sheet (filename: `P0N-YYYYMMDD.md`, local only)
- [ ] Confirm new lines landed in `data/logs/requests.jsonl`
- [ ] Tag the worst finding (`trust-breaking` / `core-task blocker` / `improvement`)
- [ ] If a question was excellent, queue it for `data/eval/questions.yaml`
      (expected keywords + source family) — do not add third-party text

## 6. What “good enough to invite the next person” means

Stop and fix before the next session if you see:

- empty answer or error banner on a fallback prompt
- JSON-LD / workflow panel failing to open on a generation prompt
- citations that are obviously the wrong source family (e.g. example JSON
  for a NE:ONE docker question)

Do **not** change retrieval or prompts mid-round unless a fallback is broken.
Otherwise later sessions cannot be compared.
