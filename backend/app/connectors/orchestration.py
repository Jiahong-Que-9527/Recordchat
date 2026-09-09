"""Workflow orchestration entrypoints decoupled from RAG retrieval (#32)."""

from __future__ import annotations

from app.connectors.recordforge import RecordForgeConnector, get_recordforge_connector
from app.connectors.workflow import WorkflowResult
from app.core.config import Settings


def run_synthetic_data_workflow(
    query: str,
    *,
    connector: RecordForgeConnector | None = None,
    settings: Settings | None = None,
) -> WorkflowResult:
    """Execute the synthetic-generation workflow behind the Connector ABC."""
    active = connector or get_recordforge_connector(settings=settings)
    return active.execute_synthetic_generation(query)
