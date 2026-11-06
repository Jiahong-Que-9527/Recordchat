# v0.3.1 Trial-user auth — execution brief

**Status:** open (2026-09-13) — coding on `feat/v0.3.1-trial-auth`  
**Owner docs:** this file wins over [v03_sketch.md](v03_sketch.md) §3.1 and over
older GitHub issue bodies when they disagree. Sketch items 3.2–3.7 stay frozen.  
**Decision record:** [adr/0004-trial-user-auth.md](adr/0004-trial-user-auth.md)

This is **public trial accounts on our domain**. It is not a closed invite-only
beta, not chat persistence, and not a full SaaS.

Work order is mandatory: **AUTH-01 → AUTH-02 → AUTH-03 → AUTH-04 → AUTH-05**.
Each step must leave `AUTH_MODE=off` bootable without Clerk keys.

## 1. Goal

A visitor using only `https://<our-domain>` can:

1. Land on a login page (unauthenticated `/` redirects to `/sign-in`).
2. Sign up as a **trial** user (email + password + email verification) **or**
   sign in with an admin-provisioned account (unique temporary password, must
   change before chatting).
3. Use RecordChat under per-user quotas.
4. Change their password and sign out themselves.
5. Later be promoted `plan=trial → plan=user` without a new account or password
   reset.

Testers already **are** trial users. The same accounts become regular users.

## 2. Non-goals (do not implement)

- Chat body persistence / server-side conversation memory (sketch 3.2)
- Live ONE Record Server writes (sketch 3.6)
- Live AviationLakehouse (sketch 3.7)
- Billing, teams, SSO, multi-tenant orgs, Clerk webhooks
- Cloudflare Access in front of the **user** hostname
- Publishing backend `:8000` or Qdrant `:6333` to the internet
- Renaming `/chat` fields or moving orchestration out of `pipeline.py`
- Ingesting `data/raw/_staging/`
- Redis / a second replica / a separate user-service

## 3. Why this slice exists

v0.2.6 is a localhost demo. A public hostname without accounts, quotas, ingest
isolation, or log redaction would expose `/ingest`, raw questions, and
unbounded LLM spend.

v0.3 sketch §3.1 said “auth + sessions”. Product direction (2026-09-13) is
**trial-user product now**, so “real usage” is a plan/quota change, not a
second identity project.

## 4. Architecture (locked decisions — do not re-litigate in code)

```text
User browser
  → HTTPS Cloudflare Edge (TLS, WAF, bot / rate-limit)
  → Cloudflare Tunnel (outbound cloudflared only)
  → Next.js frontend :3000          ← only published service
        /sign-in  /sign-up  /account  /admin  /privacy  /
        BFF /api/chat  /api/models  /api/me  /api/admin/*
        Clerk session cookie (HttpOnly, Secure, SameSite=Lax)
        internal HMAC JWT (identity only) → backend
  → FastAPI :8000 (Docker network only)
        Depends: verify JWT, load user from DB, quota, length, kill switch
        then pipeline.answer_stream()     ← unchanged /chat JSON
  → Qdrant :6333 (Docker network + API key)
```

Identity **never** enters `ChatRequest`. Handlers stay thin.

### 4.1 Two onboarding paths, one user row

| Path | Who | First-time UX | Defaults |
|---|---|---|---|
| Self-serve sign-up | Trial visitors | Domain → `/sign-up` → verify email → set password | `role=user`, `plan=trial`, `status=active` |
| Admin provision | People you onboard | Domain → `/sign-in` with emailed temp password → forced change | `role=user`, `plan=trial` (or `user` if admin set it) |

Clerk Access mode is **Open**. Email + password. Verify-at-sign-up on. Social
login off. Disposable-email and subaddress blocking on in the Clerk Dashboard
(manual ops, not code).

Official refs:

- [Clerk access modes](https://clerk.com/docs/guides/secure/restricting-access)
- [createUser with password](https://clerk.com/docs/reference/backend/user/create-user)
- [Force password reset session task](https://clerk.com/changelog/2025-12-19-force-password-reset)
- [Cloudflare Tunnel publish](https://developers.cloudflare.com/tunnel/get-started/)
- [Cloudflare WAF](https://developers.cloudflare.com/waf/)
- [Qdrant API keys](https://qdrant.tech/documentation/security/)
- Next.js [`headers`](https://nextjs.org/docs/app/api-reference/config/next-config-js/headers)

### 4.2 `role` vs `plan` (do not collapse)

```text
users.role  = user | admin     # authorization for /admin and /internal/admin
users.plan  = trial | user     # quotas and feature flags
users.status = active | revoked
```

There is **no** `plan=admin`. An operator is `role=admin` and usually
`plan=user`. Chat quotas always follow `plan`, never `role`.

| Plan | Chat / UTC day | Allowed `model` | RecordForge |
|---|---|---|---|
| `trial` | `CHAT_DAILY_LIMIT_TRIAL` (default 30) | `deepseek-v4-flash` only | forced `local` |
| `user` | `CHAT_DAILY_LIMIT_USER` (default 100) | flash + pro | allowed |

`users.daily_quota` non-null overrides the plan default for that user.

Promotion: `UPDATE users SET plan='user'`. Same Clerk user, same password.

### 4.3 How a Clerk user becomes a SQLite row

**No Clerk webhooks in this slice.** Sync is pull-based:

1. After Clerk session is valid, the BFF calls
   `POST {INTERNAL_API_BASE_URL}/internal/users/ensure` with the internal JWT.
2. Backend upserts `users` on `idp_user_id = JWT.sub`.
   - Insert: `role=user`, `plan=trial`, `status=active`, `email_hash=sha256(email)`.
   - Existing row: update `email_hash` if present; **do not** reset plan/role/status.
3. Admin provision also inserts immediately after `createUser` (same upsert,
   with the plan/role the admin chose).

Email for hashing comes from the verified Clerk session on the BFF, passed as
JWT claim `email_hash` (already hashed — **never put raw email in the JWT**).

```text
BFF:
  email_hash = sha256(lowercase(trim(clerk_email)) + EMAIL_HASH_PEPPER)
  JWT.email_hash = email_hash
```

Pepper is `EMAIL_HASH_PEPPER` (backend and BFF share it; default to
`INTERNAL_AUTH_SECRET` if unset). Admin UI may show `email_prefix` stored
separately: first 2 chars of local-part + domain, e.g. `ab***@iata.org`.
Store `email_prefix` on insert from the BFF body of `/internal/users/ensure`:

```json
{ "email_prefix": "ab***@example.com" }
```

The JSON body of `/internal/users/ensure` is the only place a prefix is sent.
It is not a raw inbox.

### 4.4 Trust boundary and revoke

JWT is **identity only**. Backend **always** reloads `role`, `plan`, `status`,
`daily_quota` from SQLite. Do not authorize from JWT claims other than `sub`.

```text
Browser Clerk cookie
  → Next middleware: Clerk session present? else redirect /sign-in
  → BFF: auth(); if missing 401
  → BFF signs JWT (sub, email_hash, iss, aud, iat, exp, jti)
  → BFF POST /internal/users/ensure
  → BFF POST /chat/stream with Authorization: Bearer <jwt>
  → Backend: verify JWT (HS256, iss, aud, exp, leeway 30s)
  → Backend: SELECT user WHERE idp_user_id = sub
       missing → treat as ensure miss, 401
       status=revoked → 401 { "error": "revoked" }
  → quota / length / kill switch
  → pipeline.answer_stream(...)
```

Revoke (immediate for chat):

1. Clerk `users.banUser(idp_user_id)` (invalidates Clerk sessions).
2. `users.status = revoked`, `revoked_at = now`.
3. Backend DB check fails on the next `/chat` even if a 90s JWT is still valid.

Next.js middleware cannot see SQLite. That is OK: Clerk ban kills the cookie
on the next document request; chat is already gated by the DB.

### 4.5 Internal JWT

| Field | Value |
|---|---|
| alg | HS256 |
| header | `Authorization: Bearer <token>` only |
| iss | `recordchat-bff` |
| aud | `recordchat-backend` |
| sub | Clerk user id (`user_...`) |
| email_hash | hex sha256 (see 4.3) |
| jti | uuid4 |
| iat / exp | now / now+`INTERNAL_JWT_TTL_SECONDS` (default 90) |
| leeway | 30 seconds |
| secret | `INTERNAL_AUTH_SECRET` (≥32 random bytes). Missing secret + `AUTH_MODE=enforced` → refuse to boot chat (503), not “open”. |

Do **not** put `role`, `plan`, or `status` in the JWT.

### 4.6 AUTH_MODE

| Mode | Frontend | BFF | Backend |
|---|---|---|---|
| `off` (default, local/CI) | No ClerkProvider required; `/` is the chat | No JWT; no ensure | Skip auth Depends; `/ingest` stays public as today |
| `enforced` | Clerk required; unauthenticated `/` → `/sign-in` | JWT + ensure | JWT required on `/chat`, `/chat/stream`, `/internal/*` except ingest-token route |

`off` must not need Clerk env vars. Tests default to `off` unless a test sets
`enforced` and injects a secret + JWT.

### 4.7 Quotas and 429

Single backend replica. Daily counters in SQLite. In-flight stream slots in
**process memory** (restart clears them — acceptable).

Before calling `pipeline.answer_stream`:

1. Kill switch or daily USD budget exceeded → **503**
   `{ "error": "unavailable", "retry_after_seconds": 3600 }`
2. `status != active` → **401** `{ "error": "revoked" }`
3. `len(message) > CHAT_MAX_MESSAGE_CHARS` or history turns/chars over cap → **400**
   `{ "error": "payload_too_large" }`
4. In-memory `streams[user_id] >= CHAT_MAX_CONCURRENT_PER_USER` (default 1) → **429**
5. In-memory global streams >= `CHAT_GLOBAL_MAX_STREAMS` (default 10) → **429**
6. `usage_daily.request_count` for UTC today >= effective quota → **429**
   `{ "error": "rate_limited", "retry_after_seconds": <seconds to next UTC midnight> }`

Always send `Retry-After` on 429/503. Increment `usage_daily` **before** the
LLM call (failed calls still count). Decrement the in-memory stream slot in
`finally`.

Trial plan: if client `model` is not flash, **ignore it** and use flash. If
client `synthetic_mode=recordforge`, **force `local`**. Do this in the backend
Depends/handler, not in `pipeline.py` business logic — pass the already-clamped
values into `answer_stream`.

Per-IP limits (BFF, in-memory):

- `/sign-in` `/sign-up` are Clerk-hosted; still rate-limit `/api/chat` by
  `CF-Connecting-IP` or first `X-Forwarded-For` hop, hashed:
  60 chats / hour / IP. 429 as above.

Token USD estimate: prefer provider usage if the LLM client exposes it later;
for v0.3.1 use `estimated_usd += (len(message)+len(answer)) / 4 * USD_PER_TOKEN`
with `LLM_USD_PER_1K_TOKENS` default `0.002`. Budget cap uses this estimate.

### 4.8 Admin provision and forced password change

Admin UI (`/admin`, `role=admin` only):

1. Submit email (+ optional plan).
2. BFF generates a 20-char password from `secrets.token_urlsafe(24)` (trim to
   20+). Never a shared default. Never log it.
3. `clerkClient.users.createUser({ emailAddress: [email], password, skipPasswordChecks: false })`.
4. Set Clerk `publicMetadata.must_reset_password = true`.
5. Upsert local user with chosen plan.
6. **Response JSON includes `temporary_password` once.** Operator sends it out
   of band (mail/IM). We do not email passwords from this app.

On login, if `publicMetadata.must_reset_password`, the app redirects to
`/account?force=1` and **blocks `/api/chat`** (BFF 403
`{ "error": "password_change_required" }`) until the user changes the password
via Clerk `user.updatePassword`. Then BFF calls Clerk Backend
`updateUserMetadata` to set `must_reset_password: false`.

Forgot-password is Clerk `<SignIn />` built-in. Do not write a custom reset
mailer.

### 4.9 Ingest isolation

| Mode | `POST /ingest` | `POST /internal/ingest` |
|---|---|---|
| `off` | kept (today’s `make ingest`) | optional alias |
| `enforced` | **not registered** | requires header `X-Ingest-Token: $INGEST_TOKEN` |

`INGEST_ALLOW_RESET` default `true` when `off`, **must be `false`** in public
compose. `make ingest` sends the token when the env var is set:

```bash
curl -fsS -X POST "$(BACKEND_URL)/ingest" \
  ${INGEST_TOKEN:+-H "X-Ingest-Token: $(INGEST_TOKEN)"}
```

When enforced, `BACKEND_URL` stays `http://127.0.0.1:8000` on the host and the
path is `/internal/ingest`. Makefile switches path on `AUTH_MODE`.

### 4.10 Logging

Default `RECORDCHAT_REQUEST_LOG_INCLUDE_QUERY=false`. `log_chat_request` event
**must not** contain `query`, `message`, `answer`, `history`, or prompt text.

Required fields: `ts`, `event`, `request_id`, `user_id` (idp id or `local-dev`),
`query_hash` (sha256 of raw query, no pepper), `query_len`, `query_type`,
`model`, `latency_ms`, `cited_chunk_ids`, `source_count`, `history_turns`,
`prompt_tokens_est`, `completion_tokens_est`.

`pipeline.py` may still receive the raw query for RAG; it must pass a redacted
dict into `log_chat_request`.

## 5. Contract changes (additive only)

Do **not** rename `/chat` fields. Do **not** put `user_id` on `ChatRequest`.

| Layer | Change |
|---|---|
| Frontend routes | `/sign-in`, `/sign-up`, `/account`, `/admin`, `/privacy`; `/` requires session when enforced |
| BFF | `/api/chat`, `/api/models`, `/api/me`, `/api/admin/*` |
| Backend | `POST /internal/users/ensure`; auth Depends on `/chat` and `/chat/stream` when enforced |
| `/ingest` | see 4.9 |
| Logs | no raw query |
| `/chat` JSON | unchanged |

New **non-chat** error bodies (BFF and backend). These are not ChatResponse.

```json
{ "error": "unauthorized" }
{ "error": "revoked" }
{ "error": "rate_limited", "retry_after_seconds": 3600 }
{ "error": "payload_too_large" }
{ "error": "unavailable", "retry_after_seconds": 3600 }
{ "error": "password_change_required" }
```

Frontend stream path: if BFF gets a non-SSE error status, map to the existing
AI SDK error (`type: "error"`), show the `error` code as user-facing copy
(quota / sign-in / try later). Do not dump stack traces.

## 6. Work order

### AUTH-01 — Hardening that blocks any public hostname

Do this before Clerk. Local demo must still run.

**Compose / images**

- `qdrant/qdrant:v1.19.1` (not `:latest`). After `docker pull`, paste the
  image digest in a comment in `docker-compose.yml`.
- Set `QDRANT__SERVICE__API_KEY` from `.env` (`QDRANT_API_KEY` same value).
- `backend/app/core/config.py`: add `qdrant_api_key: str = ""`.
- `backend/app/rag/retriever.py`: `QdrantClient(url=..., api_key=settings.qdrant_api_key or None)`.
  `:memory:` mode ignores the key.
- Pin `python:3.11-slim` and `node:20-alpine` by tag (digest comment OK).
- Do **not** add cloudflared yet (AUTH-05). Keep `127.0.0.1` port publishes.

**Frontend supply chain**

- `frontend/Dockerfile` deps stage: `COPY package.json package-lock.json ./`
  then `npm ci` (not `npm install`).
- Upgrade `next` to **16.3.5** (minimum 16.3.3). Run `npm run build`.
- `npm audit`: no unfixed **critical**. High: fix or record the advisory id in
  the PR description. Re-test Mermaid, JSON-LD canvas, streaming chat.

**Security headers** — `frontend/next.config.mjs` `headers()` for `/:path*`:

```text
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://*.clerk.accounts.dev https://*.clerk.com;
  connect-src 'self' https://*.clerk.accounts.dev https://*.clerk.com;
  img-src 'self' data:;
  style-src 'self' 'unsafe-inline';
  frame-src 'self' https://*.clerk.accounts.dev https://*.clerk.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self'
```

AUTH-01 may use `'unsafe-inline'` for scripts; AUTH-02 can tighten to nonces
if Clerk allows. Do not block Mermaid (inline SVG/CSS).

**Logs**

- `pipeline.py` `log_chat_request` dicts: drop `"query": query`. Add
  `query_hash`, `query_len`, `request_id` (uuid if missing).
- Gate raw query on `RECORDCHAT_REQUEST_LOG_INCLUDE_QUERY`.
- Tests: a unit test that the helper used by pipeline does not include `query`
  when the flag is false. Do not require a live LLM.

**`.env.example`**

- Add the AUTH-01 vars (`QDRANT_API_KEY`, log flag).
- Delete or strike the “VPS + NEXT_PUBLIC_API_BASE_URL=http://\<vps\>:8000”
  recipe. Comment: browser talks only to the frontend origin; BFF uses
  `INTERNAL_API_BASE_URL`.

**Tests / verify**

- `uv run pytest -q` from `backend/`
- `npm run build` from `frontend/`
- Existing chat tests still pass with redacted logs

### AUTH-02 — Clerk session, pages, password UX

**Dashboard (ops, document in README later):** create a Clerk application,
Open access mode, email+password, verify at sign-up, no social, block
disposable emails.

**Code**

- Dependency: `@clerk/nextjs` current major compatible with Next 16.
- `frontend/app/layout.tsx`: wrap with `ClerkProvider` only when
  `AUTH_MODE=enforced` **or** Clerk publishable key is set. When `off` and no
  key, render children as today.
- `frontend/middleware.ts`: if `AUTH_MODE !== enforced`, `NextResponse.next()`.
  If enforced, `clerkMiddleware` protecting `/`, `/admin`, `/account`,
  `/api/chat`, `/api/me`, `/api/admin`, `/api/models`. Public:
  `/sign-in(.*)`, `/sign-up(.*)`, `/privacy`, Clerk internals, Next static.
- Pages (Clerk catch-all):
  - `frontend/app/sign-in/[[...sign-in]]/page.tsx` — `<SignIn />`
  - `frontend/app/sign-up/[[...sign-up]]/page.tsx` — `<SignUp />`
  - `frontend/app/account/page.tsx` — `<UserProfile />` or password fields +
    Sign out. Honor `?force=1` copy: “Set your own password before chatting.”
  - `frontend/app/privacy/page.tsx` — short notice: no chat-body storage;
    logs omit question text; trial quotas; not an IATA product.
- `frontend/app/page.tsx`: first-visit banner with the same privacy one-liner
  + link to `/privacy`. If `must_reset_password`, redirect to `/account?force=1`.
- Sign-out control in the existing header/sidebar.

**Env (frontend)**

```text
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
AUTH_MODE=off
```

**Tests:** `npm run build`. Manual AUTH-02 check list is in §8. No backend
Clerk mock required yet.

### AUTH-03 — Internal JWT, SQLite, quotas

New modules (not inside `pipeline.py`):

```text
backend/app/core/internal_auth.py
    sign_internal_jwt(...)     # used only in tests; production signer is BFF
    verify_internal_jwt(token) -> {sub, email_hash}
    fastapi Depends get_auth_user() -> LocalUser | None
        AUTH_MODE=off → None (handlers behave as today)
        missing/invalid → 401
        load SQLite; revoked → 401

backend/app/core/quota.py
    check_and_begin(user, message, history) -> None  # raises HTTPException
    end_stream(user_id) -> None
    clamp_model_and_mode(user, model, synthetic_mode) -> (model, mode)

backend/app/db/sqlite.py
    connect, init schema, upsert_user, get_user, increment_usage

backend/app/api/internal_users.py
    POST /internal/users/ensure
```

SQLite file: `RECORDCHAT_DB_PATH` default `data/app/recordchat.db`. Docker:
writable mount `./data/app:/app/data/app` (do not make all of `data/` writable).

**Schema** (no chat bodies):

```sql
users (
  id            TEXT PRIMARY KEY,
  idp_user_id   TEXT UNIQUE NOT NULL,
  email_hash    TEXT NOT NULL,
  email_prefix  TEXT NOT NULL DEFAULT '',
  role          TEXT NOT NULL DEFAULT 'user',    -- user | admin
  plan          TEXT NOT NULL DEFAULT 'trial',   -- trial | user
  status        TEXT NOT NULL DEFAULT 'active',  -- active | revoked
  daily_quota   INTEGER,
  created_at    TEXT NOT NULL,
  revoked_at    TEXT
);

usage_daily (
  user_id                 TEXT NOT NULL,
  day                     TEXT NOT NULL,
  request_count           INTEGER NOT NULL DEFAULT 0,
  prompt_tokens_est       INTEGER NOT NULL DEFAULT 0,
  completion_tokens_est   INTEGER NOT NULL DEFAULT 0,
  estimated_usd           REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);

audit_events (
  id              TEXT PRIMARY KEY,
  ts              TEXT NOT NULL,
  actor_user_id   TEXT,
  action          TEXT NOT NULL,
  ip_hash         TEXT,
  request_id      TEXT,
  metadata_json   TEXT
);
```

`audit_events.action` values: `ensure`, `chat_ok`, `chat_429`, `chat_401`,
`revoke`, `provision`, `plan_change`, `kill_switch`.

**BFF `frontend/app/api/chat/route.ts`** when enforced:

1. `auth()` from Clerk; 401 if missing.
2. If `must_reset_password` public metadata → 403 `password_change_required`.
3. Cap message/history (same numbers as backend).
4. Sign JWT; `POST /internal/users/ensure` with `{ email_prefix }`.
5. `fetch(backend /chat/stream)` with `Authorization` and `X-Request-Id`.
6. `/chat` JSON body fields stay `message`, `model`, `history`, `synthetic_mode`.
7. Translate 401/403/429/503 JSON into the stream error path.

**`frontend/app/api/models/route.ts`:** proxy `GET {backend}/models`, filter
to flash-only when the ensured user’s plan is `trial`.

**`frontend/app/api/me/route.ts`:** `{ plan, role, status, quota, used_today }`
for the banner (“12 / 30 trial questions today”).

**`backend/app/api/chat.py`:** Depends `get_auth_user`, `check_and_begin`,
`clamp_model_and_mode`, then existing `answer` / `answer_stream`. No prompts
here.

**Tests** (`backend/tests/test_auth_quota.py`):

- `AUTH_MODE=off`: `POST /chat` without JWT still 200/422 as today (use existing
  fake LLM fixtures).
- `AUTH_MODE=enforced`, no JWT: 401.
- Bad signature / wrong aud: 401.
- Valid JWT, unknown user that ensure would create: chat Depends without ensure
  → 401; after ensure → proceeds to pipeline mock.
- Revoked user: 401 `revoked`.
- Message 4001 chars: 400 `payload_too_large`.
- Daily quota 0 remaining: 429 + Retry-After.
- Concurrent: second overlapping stream 429 (call `check_and_begin` twice).
- Trial clamp: request `model=deepseek-v4-pro` → pipeline receives flash.
- Trial clamp: `synthetic_mode=recordforge` → local.
- Log helper: no `query` key.
- `/ingest` with `enforced` and no token: 401/404 (AUTH-04 may land the 404).

Frontend: `npm run build`. Optional: a small test that `/api/chat` without
cookie returns 401 when `AUTH_MODE=enforced` (skip if no Clerk in CI).

### AUTH-04 — Ingest isolation and admin UI

- When `enforced`, do not `include_router(ingest.router)` on `/ingest`.
  Register `POST /internal/ingest` with `X-Ingest-Token` compare
  `hmac.compare_digest`.
- Makefile: if `AUTH_MODE=enforced`, POST `/internal/ingest` with token.
- `INGEST_ALLOW_RESET=false` in the public `.env.example` comment.

**Admin BFF + pages** (`role=admin` checked via `/internal/users/ensure` + DB):

| Route | Action |
|---|---|
| `GET /api/admin/users` | list: prefix, plan, status, used_today, quota |
| `POST /api/admin/users` | body `{ email, plan? }` → Clerk createUser + upsert; return `{ idp_user_id, temporary_password }` once |
| `POST /api/admin/users/{idp_id}/revoke` | Clerk ban + status=revoked |
| `POST /api/admin/users/{idp_id}/plan` | body `{ plan, daily_quota? }` |
| `GET /api/admin/usage` | totals: DAU, request_count, estimated_usd, 429 count — **no raw questions** |

`frontend/app/admin/page.tsx`: those four actions. First admin: set
`ADMIN_IDP_USER_IDS=user_xxx,user_yyy` env; `ensure` promotes those ids to
`role=admin` if not revoked. Do not hardcode emails.

Tests: ingest without token in enforced mode; admin route with `role=user`
JWT → 403; provision + revoke round-trip against a mocked Clerk client.

### AUTH-05 — Public hostname

- Compose service `cloudflared` image `cloudflare/cloudflared:2025.8.1` or the
  current stable **pinned tag** (not `:latest`), `command: tunnel --no-autoupdate run`,
  `TUNNEL_TOKEN` from env. Network: same Docker network as frontend.
  Ingress (dashboard published application): hostname → `http://frontend:3000`
  only. Catch-all 404. **Never** frontend-publish backend or qdrant.
- Optional: stop publishing `frontend:3000` to the host on the public compose
  overlay; keep `127.0.0.1` publishes in the default compose for local.
- Cloudflare Dashboard (ops, write into `docs/v03_ops.md` short checklist):
  WAF Free Managed Ruleset; rate-limit `/sign-up*` and `/api/chat`; TLS.
- `CORS_ORIGINS=https://<domain>`.
- `NEXT_PUBLIC_API_BASE_URL` empty.
- Container hardening (may start in AUTH-01, finish here): `cap_drop: ALL`,
  `security_opt: [no-new-privileges:true]`, memory/cpu limits.

Ops checklist file: `docs/v03_ops.md` (Tunnel create, Clerk Open mode, first
admin id, kill switch, rollback). Keep it short.

## 7. Environment variables (additive)

```text
AUTH_MODE=off
INTERNAL_AUTH_SECRET=
INTERNAL_JWT_TTL_SECONDS=90
EMAIL_HASH_PEPPER=
ADMIN_IDP_USER_IDS=

NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up

CHAT_DAILY_LIMIT_TRIAL=30
CHAT_DAILY_LIMIT_USER=100
CHAT_MAX_CONCURRENT_PER_USER=1
CHAT_MAX_MESSAGE_CHARS=4000
CHAT_MAX_HISTORY_TURNS=6
CHAT_GLOBAL_MAX_STREAMS=10
LLM_DAILY_BUDGET_USD=15
LLM_USD_PER_1K_TOKENS=0.002
LLM_KILL_SWITCH=false

INGEST_TOKEN=
INGEST_ALLOW_RESET=true
QDRANT_API_KEY=
RECORDCHAT_DB_PATH=data/app/recordchat.db
RECORDCHAT_REQUEST_LOG=data/logs/requests.jsonl
RECORDCHAT_REQUEST_LOG_INCLUDE_QUERY=false

TUNNEL_TOKEN=
CORS_ORIGINS=http://localhost:3000
INTERNAL_API_BASE_URL=http://backend:8000
NEXT_PUBLIC_API_BASE_URL=
```

Public deploy: `AUTH_MODE=enforced`, `INGEST_ALLOW_RESET=false`,
`CORS_ORIGINS=https://<domain>`, non-empty secrets, `NEXT_PUBLIC_API_BASE_URL` empty.

## 8. File list (stay inside this)

| Path | Step | Why |
|---|---|---|
| `docker-compose.yml` | 01, 05 | pin Qdrant, API key, later cloudflared |
| `.env.example` | 01–05 | new vars; remove public :8000 recipe |
| `frontend/Dockerfile` | 01 | `npm ci` + lockfile |
| `frontend/package.json` | 01, 02 | next 16.3.5; `@clerk/nextjs` |
| `frontend/next.config.mjs` | 01 | headers |
| `backend/app/core/config.py` | 01, 03 | settings |
| `backend/app/rag/retriever.py` | 01 | Qdrant API key |
| `backend/app/core/request_log.py` | 01 | include-query flag |
| `backend/app/rag/pipeline.py` | 01 | redact query in log dict |
| `frontend/middleware.ts` | 02 | Clerk gate |
| `frontend/app/layout.tsx` | 02 | ClerkProvider |
| `frontend/app/sign-in/**`, `sign-up/**`, `account/`, `privacy/` | 02 | UX |
| `frontend/app/page.tsx` | 02, 03 | banner, force-reset, 429 copy |
| `frontend/app/api/chat/route.ts` | 03 | JWT, ensure, caps |
| `frontend/app/api/models/route.ts` | 03 | plan-filtered models |
| `frontend/app/api/me/route.ts` | 03 | quota banner |
| `frontend/lib/internalJwt.ts` | 03 | HS256 signer (server-only) |
| `backend/app/core/internal_auth.py` | 03 | verify JWT |
| `backend/app/core/quota.py` | 03 | limits |
| `backend/app/db/sqlite.py` | 03 | schema |
| `backend/app/api/internal_users.py` | 03 | ensure |
| `backend/app/api/chat.py` | 03 | thin Depends |
| `backend/app/main.py` | 03, 04 | mount routers by mode |
| `backend/tests/test_auth_quota.py` | 03, 04 | cases in AUTH-03 |
| `backend/tests/test_ingest_auth.py` | 04 | ingest token |
| `Makefile` | 04 | ingest path + token |
| `frontend/app/admin/page.tsx` | 04 | admin UI |
| `frontend/app/api/admin/**` | 04 | admin BFF |
| `docs/v03_ops.md` | 05 | Tunnel / Clerk / rollback ops |
| `docs/project_plan.md`, `AGENTS.md`, `architecture.md` | this slice | status |

Do not touch retrieval ranking, provider ABCs, or JSON-LD templates except log
redaction / `request_id`.

## 9. Definition of done

- [ ] AUTH-01: Qdrant `v1.19.1` + API key; Next ≥ 16.3.3; `npm ci`; headers;
      logs omit `query` by default; pytest + frontend build green
- [ ] AUTH-02: domain-style routes work locally with Clerk in enforced mode;
      `off` still works with no keys
- [ ] AUTH-03: ensure upsert, JWT identity-only, quotas, trial clamps, tests
      listed in AUTH-03 green
- [ ] AUTH-04: public `/ingest` gone when enforced; admin provision returns a
      one-time password; revoke blocks `/api/chat`
- [ ] AUTH-05: Tunnel published hostname is frontend only; ops doc exists
- [ ] `/chat` field names unchanged
- [ ] `pipeline.py` still the only orchestrator
- [ ] No chat bodies in SQLite
- [ ] `project_plan.md` / `AGENTS.md` still point at this brief until closed

## 10. Spot checks

Local `AUTH_MODE=off`:

1. `make up` without Clerk keys → chat as today
2. `What is a Piece in ONE Record?` (regression)
3. `Generate 5 synthetic shipments with pieces.` (local JSON-LD)

Enforced (staging hostname or Clerk dev keys on localhost):

1. Open origin → `/sign-in`
2. Sign up → email verify → chat as `trial`
3. Trial picker cannot actually use pro (request clamped)
4. Admin creates user → temp password shown once → login → forced change → chat
5. 31st trial question in a UTC day → 429
6. Revoke → next `/api/chat` 401
7. Promote to `user` → same password, higher quota, pro allowed
8. From an external network: `:8000`, `:6333`, `/ingest` fail
9. `make ingest` on the host with token succeeds
10. New JSONL line has `query_hash` and no `query`

## 11. Rollback

1. Stop `cloudflared` or unpublish the hostname.
2. `LLM_KILL_SWITCH=true` and rotate provider keys.
3. Clerk ban + `status=revoked` for one user.
4. Revert the feature-branch images; keep a SQLite copy from pre-deploy.

Do not roll back by binding backend/Qdrant to `0.0.0.0`.

## 12. P1 after this slice (do not sneak into AUTH-01…05)

- CSP nonces instead of `'unsafe-inline'`
- Account self-delete
- Log retention cron (14 / 90 days)
- Cloudflare Access on a **separate** `admin.` hostname
- Clerk webhook as a faster ensure path
- Chat persistence (sketch 3.2) — **new brief required**

## 13. What “user usage stage” is (not this PR)

- Set `plan=user` (per account or as the default for new sign-ups)
- Raise `CHAT_DAILY_LIMIT_USER` / `LLM_DAILY_BUDGET_USD`
- Same login, same Clerk users

No second auth system.

## 14. After this slice

Stop. Do not start sketch 3.2–3.7. Optional leftover P2: AUD-08, AUD-10,
AUD-04 ModelPicker wiring to `/api/models` if not already done in AUTH-03,
leftover `#23`.
