# ADR 0004 — Trial-user auth for public RecordChat

**Status:** accepted (2026-09-13)
**Slice:** v0.3 trial auth — [v03_execution_brief.md](../v03_execution_brief.md)

## Context

RecordChat is a localhost-bound RAG demo: no login, no quotas, unauthenticated
`/ingest`, raw query JSONL, and no security headers. The product now needs a
public HTTPS domain where **testers are trial users**, not a throwaway closed
beta. Those same accounts must graduate to regular use without a second identity
system.

Product constraints:

- Users reach RecordChat on **our domain only** (login / sign-up / chat).
- Admins may pre-create accounts with a one-time password; users then change it.
- Self-serve trial sign-up must work so the next step is “real usage”, not a
  rewrite.
- Do not persist chat bodies in v0.3.1.
- Do not auto-write ONE Record Server objects or run live ALH.
- `/chat` field names stay a hard contract; `pipeline.py` stays the only
  orchestrator.

## Decision

1. **Application identity:** self-hosted email + password on the RecordChat
   backend (scrypt hashes, SQLite sessions, HttpOnly cookie via the BFF).
   No Clerk. Invite-only is not the product model.
2. **Provisioning:** two ways onto the same user table — self-serve sign-up
   (`plan=trial`) and admin `createUser` with a unique temporary password
   (forced change on first login).
3. **Graduation:** `plan` is `trial | user` (quotas). `role` is `user | admin`
   (authorization). There is no `plan=admin`. Moving a trial account to regular
   use is a plan change, not a new auth stack.
   User rows are created on signup or admin provision. JWT is identity-only
   (`sub`); status/plan/role are always read from SQLite.
4. **Edge:** Cloudflare Tunnel + WAF in front of the Next.js frontend only.
   Backend and Qdrant stay private. **No Cloudflare Access on the user
   hostname** (it would sit in front of our login page). Access is optional on
   a separate admin hostname.
5. **Identity to the backend:** BFF reads the session cookie, looks up the
   user, and sends a short internal HMAC JWT. User id is **not** added to the
   `/chat` JSON body.
6. **Local/CI:** `AUTH_MODE=off` so the stack still boots without secrets.

## Consequences

- Public sign-up makes LLM-cost abuse the primary risk. Per-user quotas, model
  allowlists by plan, global daily budget, and a kill switch are P0.
- RecordChat holds passwords, sessions, plan, quota, usage, and audit events.
- SMTP-backed email verification is optional later; local/enforced signup
  currently marks email verified so password login can be tested without a
  mailer.
- Chat persistence, billing, SSO, and multi-tenant orgs stay out of this ADR.

## Alternatives rejected

| Option | Why not |
|---|---|
| Cloudflare Access OTP as the user identity | No password login on our domain; does not graduate to self-serve trial. |
| Invite-only first, Open later | Testers would be a different population from trial users; extra migration. |
| Self-built password/session stack | Highest defect risk for a small product; duplicates Clerk. |
| User id in `ChatRequest` | Spoofable if the backend is ever reachable; contracts `/chat` with identity. |
