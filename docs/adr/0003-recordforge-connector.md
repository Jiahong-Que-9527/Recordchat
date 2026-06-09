# ADR 0003: RecordForge Connector Abstraction

## Status

Accepted

## Context

RecordChat is moving from retrieval-only Q&A into workflow orchestration. The
next orchestration layers need to call external ecosystem tools without
hard-coding those integrations into the RAG pipeline.

RecordForge is the first planned external tool. It should eventually support
synthetic ONE Record object generation, but it is not available in every
deployment and must remain optional.

That gives us two design requirements:

1. the pipeline needs a stable connector seam before any RecordForge-specific
   client is implemented
2. missing RecordForge configuration must degrade gracefully instead of breaking
   the assistant startup path

## Decision

Introduce `backend/app/connectors/base.py` with a `Connector` abstraction that:

- exposes a connector `name`
- exposes an optional `base_url`
- reports configuration state through `describe()`
- distinguishes:
  - `ready`
  - `unconfigured`
  - `unavailable`

`core/config.py` now owns the first orchestration-specific runtime fields:

- `RECORDFORGE_URL`
- `RECORDFORGE_API_KEY`

The connector contract is intentionally minimal in this step. It is not yet a
full execution API. That comes later, once workflow intent routing and result
schemas are in place.

## Consequences

Positive:

- orchestration code can depend on a stable seam instead of direct HTTP calls
- RecordForge can stay optional in local and demo deployments
- configuration failure turns into an explicit `unconfigured` state rather than
  hidden runtime coupling

Trade-offs:

- this ADR adds one more abstraction layer before the first concrete connector
- later issues still need to define execution methods and workflow result models

## Graceful Degradation Path

If `RECORDFORGE_URL` is missing:

- the connector is treated as `unconfigured`
- the application can still start normally
- future workflow handlers should return a structured “connector not configured”
  response instead of attempting a call

If `RECORDFORGE_URL` is configured but the remote service fails:

- the connector should report `unavailable`
- workflow handlers should return a structured degraded result rather than crash

## Follow-up

- `#12` adds workflow-oriented query routing and execution intent types
- `#13` implements the first concrete RecordForge client
- `#14` adds frontend rendering and tests for workflow results
