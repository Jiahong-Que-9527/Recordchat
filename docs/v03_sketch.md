# v0.3 platform — sketch only

**Status:** §3.1 is open as **v0.3.1 trial-user auth**
([v03_execution_brief.md](v03_execution_brief.md)). §3.2–3.7 stay sketch /
not scheduled.

v0.3 is the first time RecordChat would look like a small platform instead of
a demoable assistant. Do not implement 3.2–3.7 inside the trial-auth slice.

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
| 3.1 | Auth + sessions | **Opened 2026-09-13 as trial-user accounts** (domain login, self-serve sign-up, admin temp password, `plan=trial\|user`, quotas). Chat bodies still not persisted. | Brief: [v03_execution_brief.md](v03_execution_brief.md). Keep `/chat` fields stable; identity in internal JWT headers, not the JSON body. |
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

- v0.2.6 DoD is checked — **done**
- user asks for platform work — **done** (trial-user product, 2026-09-13)
- a new `docs/v03_execution_brief.md` exists with file lists and acceptance
  tests (same shape as the ALH brief) — **done for 3.1 only**

Further v0.3 themes (3.2+) need their own brief. Do not fold them into 3.1.
