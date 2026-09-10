# v0.3 platform — sketch only

**Status:** not scheduled. Do not start this while v0.2.6 ALH is open.  
There are **no GitHub issues** on purpose.

v0.3 is the first time RecordChat would look like a small platform instead of
a demoable assistant. Keep it a sketch until ALH narrative is done and the
user explicitly asks to open a v0.3 issue.

## 1. What v0.3 is for

- multi-user / persisted usage
- operable knowledge base (versions, ingest admin)
- observable quality (tracing, eval dashboard)
- **optional** live connectors that still degrade when unconfigured

## 2. What v0.3 is not

- not an official IATA product
- not fine-tuning on third-party corpora
- not a requirement to auto-write synthetic objects into a ONE Record Server
  (product freeze: generate → display; persist is a later optional prototype)

## 3. Suggested internal order (if/when scheduled)

Do these as separate issues, each still bootable without secrets.

| Order | Theme | Intent | Notes |
|---|---|---|---|
| 3.1 | Auth + sessions | Identify a user; persist `conversation_id` | Keep `/chat` fields stable; add optional auth headers |
| 3.2 | Conversation memory | History beyond the 6-turn rewrite window | Still rewrite inside `pipeline.py` |
| 3.3 | Source versioning admin | See live canonical versions; trigger ingest | Reuse `rag/canonical.py`; no `_staging` ingest |
| 3.4 | Tracing | Request id across BFF → pipeline → providers | Build on `request_log.py` (AUD-07); OpenTelemetry later |
| 3.5 | Eval dashboard | Show `evaluate_rag.py` metrics over time | Needs the versioned eval set (already exists) |
| 3.6 | Optional live Server connector | POST generated JSON-LD to a ONE Record Server | **Only if product un-freezes persist.** New Connector ABC impl; unconfigured → blocked workflow step; never crash `/chat` |
| 3.7 | Optional live ALH connector | Push/query Bronze/Silver/Gold | After 3.6; narrative from v0.2.6 stays the fallback |

3.6–3.7 are **optional ecosystem demos**, not the definition of RecordChat.

## 4. If someone asks for “Chat → Forge → ONE Record Server” early

That is **3.6**, not ALH, and not current next work.

Minimum prototype (when explicitly requested):

```text
existing local or RecordForge generation
  → new OneRecordServerConnector
  → POST logistics-object API
  → workflow step persist = completed | failed | skipped
```

Must keep:

- `RECORDFORGE_URL` / `ONE_RECORD_SERVER_URL` optional
- unconfigured = structured blocked/skipped, not an exception
- Local JSON-LD mode still works with no Server

Do not implement 3.6 inside v0.2.6.

## 5. Open this sketch into a real plan only when

- v0.2.6 DoD is checked
- user asks for platform work
- a new `docs/v03_execution_brief.md` exists with issue numbers, file lists,
  and acceptance tests (same shape as the ALH brief)
