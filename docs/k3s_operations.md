# RecordChat WSL / K3s operations

**[房玄龄·2026-11-03]** Authorized platform migration. Actual cutover evidence and private backup locations are in the cabinet migration runbook. Never infer cutover completion from this source file.

- Development: Ubuntu WSL2, `/home/bill/src/recordchat`. Linux Node22 and uv-managed Python3.11. `recordchat-docker` uses isolated socket `/run/recordchat-docker.sock`; Docker Desktop currently has a pre-existing startup fault. Do not reset it.
- Runtime: dev single-node K3s; namespaces recordchat-staging/prod; static PVs Retain under `/var/lib/recordchat/<namespace>`. Single replica SQLite backend Recreate. No host HA.
- Private endpoints: http://dev.tail0f631b.ts.net:13000 (prod), :13001 (staging); gateway hostPort binds the verified Tailscale hostIP only. No public ingress. Verify this after networking changes.
- `deploy/k8s/overlays/<environment>` is the configuration source. Render/diff before apply. Pin release images with the release script, promote identical artifacts. Never use latest for application releases.
- Secrets are provisioned separately, never Git; staging has separate auth/Qdrant keys, synthetic accounts and budget. Real user state is prod-only. Do not copy prod DB to staging.
- Backend base + requirements.lock and frontend base + package-lock.json are pinned. Refresh requirements.lock with `uv export --frozen --no-dev --no-emit-project --no-hashes` after an intentional dependency update.
- Code rollback: previous image, provided DB schema is compatible. Data rollback requires maintenance, a current backup and an explicit compatibility check. Never enable stale avi DB after dev has accepted writes.
- Never run compose down, prune, delete PVCs or clean backup files automatically. Preserve all original source changes and failed restores.
- Application backup: SQLite online backup, Qdrant snapshot, corpus and configuration/image manifests; transfer off-host and test restore. K3s server DB and token are separate from application PV data.
- Existing auth uses local SQLite accounts. Older Clerk descriptions are historical. No chat-body persistence or live ONE Record Server writes were added.

## Verified cutover and commands (2026-11-03)

**[房玄龄·2026-11-03]** Initial application release `7883ec80d932` is running on dev. 97 backend tests and frontend production build passed. Staging: 10 real streamed answers with sources, quota 429 x3, login/logout/non-admin denial/kill switch, SQLite and Qdrant restart persistence, failed-image rollout and rollback. Prod: source DB restored with identical core table counts, 4189 vector points, login and real sourced answer passed. One synthetic prod check account remains revoked; original account was not reset. These are migration checks, not full semantic accuracy or availability certification.

```bash
cd ~/src/recordchat
source ops/env.sh
# Local development (independent local state, default kill switch on):
recordchat-docker compose -p recordchat-local -f docker-compose.yml -f docker-compose.local.override.yml up -d --no-build
# Backend tests:
(cd backend && uv run --frozen pytest -q)
# Build a new private artifact after committing changes:
python3 ops/release.py prepare
# Substitute the 12-char release printed by prepare:
python3 ops/release.py deploy --env staging --release <release>
backend/.venv/bin/python ops/verify_staging.py
python3 ops/release.py deploy --env prod --release <same-release> --staging-accepted
# Fresh off-host backup (must run while WSL is online):
python3 ops/pull_backup.py --create
```

The initial app artifact is archived under `~/.local/share/recordchat/migration/20261103-k3s`; future artifacts live in `~/.local/share/recordchat/releases/<release>`. Releases are transferred over the existing SSH alias and imported into containerd; application imagePullPolicy=Never. No GHCR credential or GitHub public push was needed. The existing GitHub workflow is updated locally for locked dependencies but has not run remotely for this branch. Review before intentionally publishing this local branch: it preserves previously untracked LICENSE and invitation text.

On dev: `systemctl start recordchat-backup.service`; daily timer runs at 03:15 Europe/Berlin. Private backup directories `/var/backups/recordchat/recordchat-prod/<UTC stamp>`, no automatic pruning. The timer writes to dev; WSL pull is a separate off-host copy and does not run while the PC is off. Monitor backup freshness and disk use. A local backup alone is not protection against losing dev.

Initial config is `/opt/recordchat/deploy/k8s`; future release deployments use `/opt/recordchat/releases/<release>/deploy/k8s`. The release printed by the deploy command and actual pod image IDs must agree. Back up both selected config root and actual Kubernetes resources. Never infer current state from an older working directory alone.

avi original private URL returns 302 to dev. Original Caddy config is preserved in `/root/recordchat-migration/20261103-k3s-final/Caddyfile.before-cutover`. All three old containers have restart=no and remain stopped. Do not start avi after dev writes unless you first maintain/stop dev and reconcile current data. See cabinet runbook for detailed restore procedure and evidence.

Known limits: single-node host failure causes downtime; current private user URL is HTTP over Tailscale; existing source metadata includes mixed_manual_sources and other legacy URLs; Next middleware/Edge build warnings remain. No public launch, PostgreSQL migration, chat persistence, live ONE Record Server writes, or file deletion was performed. Forty-eight hours of observation cannot be claimed on cutover day.

## Restore rehearsal

**[房玄龄·2026-11-03]** On dev, select a completed backup containing manifest.json and its matching runtime image artifacts. `python3 /opt/recordchat/ops/restore_rehearsal.py --backup /var/backups/recordchat/recordchat-prod/<stamp> --target recordchat-recovery-<unique>` validates the backup, restores into new Retain volumes, removes provider keys, exposes no gateway, checks SQLite and Qdrant, then scales restored workloads to zero. It uses the backed-up Kubernetes resource versions rather than today's source tree. Existing targets are rejected; failed attempts are retained. Recovery reports are stored under `/var/lib/recordchat/<target>/recovery-report.json`. Real prod restoration or reverse migration to avi still requires maintenance, current-data reconciliation and version compatibility review.
