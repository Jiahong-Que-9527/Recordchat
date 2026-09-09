"""RecordForge connector — first concrete Connector (#32 execution path).

Live HTTP generation is deferred to #13. This module still exposes a real
``execute_synthetic_generation`` path behind the ABC: it plans steps, builds a
request artifact, and reports ready / blocked / unavailable without coupling
to the RAG retrieval path.
"""

from __future__ import annotations

import re
from typing import Any

from app.connectors.base import Connector, ConnectorAvailability
from app.connectors.workflow import (
    WorkflowArtifact,
    WorkflowConnectorInfo,
    WorkflowResult,
    WorkflowStep,
)
from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_COUNT_RE = re.compile(
    r"\b(\d+)\s*(?:synthetic\s+)?(?:shipments?|pieces?|waybills?|objects?)\b",
    re.IGNORECASE,
)
_OBJECT_MARKERS = (
    ("shipments", "Shipment"),
    ("shipment", "Shipment"),
    ("pieces", "Piece"),
    ("piece", "Piece"),
    ("waybills", "Waybill"),
    ("waybill", "Waybill"),
    ("订舱", "Shipment"),
    ("货件", "Piece"),
    ("运单", "Waybill"),
)


class RecordForgeConnector(Connector):
    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        self._base_url = (settings.recordforge_url or "").strip() or None
        self._api_key = (settings.recordforge_api_key or "").strip() or None

    @property
    def name(self) -> str:
        return "recordforge"

    @property
    def base_url(self) -> str | None:
        return self._base_url

    def _connector_info(
        self,
        availability: ConnectorAvailability | None = None,
        detail: str | None = None,
    ) -> WorkflowConnectorInfo:
        descriptor = self.describe()
        return WorkflowConnectorInfo(
            name=descriptor.name,
            availability=availability or descriptor.availability,
            base_url=descriptor.base_url,
            detail=detail or descriptor.detail,
        )

    def parse_generation_intent(self, query: str) -> dict[str, Any]:
        """Extract a minimal generation request from free text."""
        q = query.lower()
        count = 1
        match = _COUNT_RE.search(query)
        if match:
            count = max(1, min(int(match.group(1)), 50))

        object_type = "Shipment"
        for marker, mapped in _OBJECT_MARKERS:
            if marker in q or marker in query:
                object_type = mapped
                break

        with_pieces = "piece" in q or "pieces" in q or "货件" in query
        return {
            "action": "generate",
            "object_type": object_type,
            "count": count,
            "options": {
                "with_pieces": with_pieces and object_type == "Shipment",
                "format": "json-ld",
            },
            "source_query": query,
        }

    def execute_synthetic_generation(self, query: str) -> WorkflowResult:
        """Run the synthetic-generation workflow path (plan + local artifact).

        Does not require a live RecordForge HTTP API yet. When unconfigured the
        result is ``blocked``; when configured the path completes a local plan
        with a ready-to-send request artifact (remote POST is #13).
        """
        intent = self.parse_generation_intent(query)
        parse_step = WorkflowStep(
            id="parse_intent",
            title="Parse generation intent",
            status="completed",
            detail=(
                f"{intent['count']} × {intent['object_type']}"
                + (" with pieces" if intent["options"].get("with_pieces") else "")
            ),
        )

        if not self.is_configured():
            info = self._connector_info()
            return WorkflowResult(
                workflow="synthetic_data_generation",
                status="blocked",
                connector=info,
                steps=[
                    parse_step,
                    WorkflowStep(
                        id="build_request",
                        title="Build RecordForge request",
                        status="skipped",
                        detail="Skipped because the connector is unconfigured.",
                    ),
                    WorkflowStep(
                        id="execute",
                        title="Execute generation",
                        status="skipped",
                        detail="Skipped because RECORDFORGE_URL is not set.",
                    ),
                ],
                artifacts=[
                    WorkflowArtifact(
                        kind="generation_intent",
                        name="parsed_intent",
                        content=intent,
                    )
                ],
                detail=(
                    "Synthetic ONE Record generation is routed to RecordForge, but "
                    "the connector is not configured in this deployment."
                ),
            )

        request_payload = {
            "connector": self.name,
            "endpoint": f"{self.base_url.rstrip('/')}/v1/generate",
            "method": "POST",
            "body": intent,
            "auth": "api_key" if self._api_key else "none",
        }
        build_step = WorkflowStep(
            id="build_request",
            title="Build RecordForge request",
            status="completed",
            detail=f"Prepared POST {request_payload['endpoint']}",
        )
        # Execution path exists; remote HTTP is intentionally not required yet.
        execute_step = WorkflowStep(
            id="execute",
            title="Execute generation",
            status="ready",
            detail=(
                "Request artifact is ready. Live HTTP submission is enabled in "
                "the RecordForge client slice (#13)."
            ),
        )
        info = self._connector_info(
            detail="RecordForge connector is configured; generation plan is ready."
        )
        logger.info(
            "RecordForge workflow planned: %s x%s (url=%s)",
            intent["object_type"],
            intent["count"],
            self.base_url,
        )
        return WorkflowResult(
            workflow="synthetic_data_generation",
            status="planned",
            connector=info,
            steps=[parse_step, build_step, execute_step],
            artifacts=[
                WorkflowArtifact(
                    kind="generation_intent",
                    name="parsed_intent",
                    content=intent,
                ),
                WorkflowArtifact(
                    kind="generation_request",
                    name="recordforge_request",
                    content=request_payload,
                ),
            ],
            detail=(
                "Structured workflow plan prepared for synthetic ONE Record "
                f"{intent['object_type']} generation."
            ),
        )


def get_recordforge_connector(settings: Settings | None = None) -> RecordForgeConnector:
    return RecordForgeConnector(settings=settings)
