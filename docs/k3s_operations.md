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
