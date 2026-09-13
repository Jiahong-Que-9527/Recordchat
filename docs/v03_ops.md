# v0.3.1 public trial — ops checklist

Do not bind backend `:8000` or Qdrant `:6333` to `0.0.0.0`. The only published
application is the Next.js frontend.

Official refs: [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/get-started/),
[WAF](https://developers.cloudflare.com/waf/),
[Clerk access modes](https://clerk.com/docs/guides/secure/restricting-access).

## 1. Clerk

1. Create a production Clerk application.
2. Access mode **Open**; email + password; verify at sign-up; no social login.
3. Enable disposable-email / subaddress blocking in the Dashboard.
4. Put `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` in `.env`.
5. First operator: copy that Clerk user id into `ADMIN_IDP_USER_IDS`.

## 2. App env (public)

```text
AUTH_MODE=enforced
INGEST_ALLOW_RESET=false
INGEST_TOKEN=<long random>
INTERNAL_AUTH_SECRET=<32+ random bytes>
EMAIL_HASH_PEPPER=<random>
CORS_ORIGINS=https://<your-domain>
NEXT_PUBLIC_API_BASE_URL=
INTERNAL_API_BASE_URL=http://backend:8000
LLM_KILL_SWITCH=false
LLM_DAILY_BUDGET_USD=15
QDRANT_API_KEY=<random>
```

Rebuild the frontend image after setting `NEXT_PUBLIC_*` keys (they are inlined
at `next build`).

## 3. Tunnel

1. Cloudflare Dashboard → Tunnels → create a remotely managed tunnel.
2. Copy the token into `TUNNEL_TOKEN`.
3. Add a **published application**: hostname `https://<your-domain>` →
   `http://frontend:3000`. Catch-all 404. Never route `:8000` or `:6333`.
4. Start: `docker compose --profile public up -d`.
5. Confirm Tunnel status is Healthy.

## 4. WAF

- Enable the Free Managed Ruleset.
- Rate-limit `/sign-up*` and `/api/chat`.
- TLS on the hostname; do not open origin 80/443 inbound.

## 5. Ingest on the host

```bash
export AUTH_MODE=enforced
export INGEST_TOKEN=...
make ingest
```

That hits `http://127.0.0.1:8000/internal/ingest` with the token. Public
`POST /ingest` is 404.

## 6. Kill switch and rollback

1. Stop public access: `docker compose --profile public stop cloudflared`
   or unpublish the hostname.
2. Stop spend: `LLM_KILL_SWITCH=true` and rotate provider keys.
3. One user: Admin → Revoke (Clerk ban + `status=revoked`).
4. Do not roll back by publishing backend/Qdrant.

## 7. Local demo (unchanged)

`AUTH_MODE=off`, no Clerk keys, `make up` without `--profile public`.
