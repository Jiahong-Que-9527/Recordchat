"""RecordForge connector — optional HTTP client for synthetic generation (#13).

When ``RECORDFORGE_URL`` is unset the connector stays ``unconfigured`` and
returns a blocked ``WorkflowResult``. When configured it POSTs to
``{base_url}/v1/generate``. Transport / remote failures map to
``availability=unavailable`` without crashing ``/chat``.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

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

_GENERATE_PATH = "/v1/generate"
_HTTP_TIMEOUT_S = 30.0

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
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        settings = settings or get_settings()
        self._base_url = (settings.recordforge_url or "").strip() or None
        self._api_key = (settings.recordforge_api_key or "").strip() or None
        self._http_client = http_client

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

    def _generate_endpoint(self) -> str:
        assert self.base_url is not None
        return f"{self.base_url.rstrip('/')}{_GENERATE_PATH}"

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _post_generate(self, intent: dict[str, Any]) -> httpx.Response:
        endpoint = self._generate_endpoint()
        headers = self._auth_headers()
        if self._http_client is not None:
            return self._http_client.post(endpoint, json=intent, headers=headers)
        return httpx.post(
            endpoint,
            json=intent,
            headers=headers,
            timeout=_HTTP_TIMEOUT_S,
        )

    @staticmethod
    def _objects_from_response(payload: Any) -> list[Any]:
        """Normalize common RecordForge response shapes into an object list."""
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        for key in ("objects", "items", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        if "@type" in payload or "@context" in payload:
            return [payload]
        return []

    def execute_synthetic_generation(self, query: str) -> WorkflowResult:
        """Plan and (when configured) execute remote synthetic generation."""
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

        endpoint = self._generate_endpoint()
        request_payload = {
            "connector": self.name,
            "endpoint": endpoint,
            "method": "POST",
            "body": intent,
            "auth": "api_key" if self._api_key else "none",
        }
        build_step = WorkflowStep(
            id="build_request",
            title="Build RecordForge request",
            status="completed",
            detail=f"Prepared POST {endpoint}",
        )
        intent_artifact = WorkflowArtifact(
            kind="generation_intent",
            name="parsed_intent",
            content=intent,
        )
        request_artifact = WorkflowArtifact(
            kind="generation_request",
            name="recordforge_request",
            content=request_payload,
        )

        try:
            response = self._post_generate(intent)
        except httpx.TimeoutException as exc:
            logger.warning("RecordForge request timed out: %s", exc)
            unavailable = self.unavailable_result(f"RecordForge request timed out: {exc}")
            return WorkflowResult(
                workflow="synthetic_data_generation",
                status="failed",
                connector=self._connector_info(
                    availability=unavailable.availability,
                    detail=unavailable.detail,
                ),
                steps=[
                    parse_step,
                    build_step,
                    WorkflowStep(
                        id="execute",
                        title="Execute generation",
                        status="failed",
                        detail=unavailable.detail,
                    ),
                ],
                artifacts=[intent_artifact, request_artifact],
                detail=unavailable.detail,
            )
        except httpx.HTTPError as exc:
            logger.warning("RecordForge request failed: %s", exc)
            unavailable = self.unavailable_result(f"RecordForge request failed: {exc}")
            return WorkflowResult(
                workflow="synthetic_data_generation",
                status="failed",
                connector=self._connector_info(
                    availability=unavailable.availability,
                    detail=unavailable.detail,
                ),
                steps=[
                    parse_step,
                    build_step,
                    WorkflowStep(
                        id="execute",
                        title="Execute generation",
                        status="failed",
                        detail=unavailable.detail,
                    ),
                ],
                artifacts=[intent_artifact, request_artifact],
                detail=unavailable.detail,
            )

        if response.status_code >= 400:
            detail = (
                f"RecordForge returned HTTP {response.status_code}"
                + (f": {response.text[:200]}" if response.text else "")
            )
            logger.warning("RecordForge unavailable: %s", detail)
            unavailable = self.unavailable_result(detail)
            return WorkflowResult(
                workflow="synthetic_data_generation",
                status="failed",
                connector=self._connector_info(
                    availability=unavailable.availability,
                    detail=unavailable.detail,
                ),
                steps=[
                    parse_step,
                    build_step,
                    WorkflowStep(
                        id="execute",
                        title="Execute generation",
                        status="failed",
                        detail=detail,
                    ),
                ],
                artifacts=[intent_artifact, request_artifact],
                detail=detail,
            )

        try:
            payload = response.json()
        except ValueError:
            detail = "RecordForge returned a non-JSON response."
            unavailable = self.unavailable_result(detail)
            return WorkflowResult(
                workflow="synthetic_data_generation",
                status="failed",
                connector=self._connector_info(
                    availability=unavailable.availability,
                    detail=unavailable.detail,
                ),
                steps=[
                    parse_step,
                    build_step,
                    WorkflowStep(
                        id="execute",
                        title="Execute generation",
                        status="failed",
                        detail=detail,
                    ),
                ],
                artifacts=[intent_artifact, request_artifact],
                detail=detail,
            )

        objects = self._objects_from_response(payload)
        artifacts: list[WorkflowArtifact] = [
            intent_artifact,
            request_artifact,
            WorkflowArtifact(
                kind="generation_result",
                name="recordforge_response",
                content=payload if isinstance(payload, (dict, list)) else {"raw": payload},
            ),
        ]
        if objects:
            artifacts.append(
                WorkflowArtifact(
                    kind="generated_objects",
                    name="synthetic_objects",
                    content=objects,
                )
            )

        execute_step = WorkflowStep(
            id="execute",
            title="Execute generation",
            status="completed",
            detail=(
                f"RecordForge returned {len(objects)} object(s)"
                if objects
                else "RecordForge call completed"
            ),
        )
        info = self._connector_info(
            detail="RecordForge connector completed remote generation."
        )
        logger.info(
            "RecordForge workflow completed: %s x%s (url=%s, objects=%s)",
            intent["object_type"],
            intent["count"],
            self.base_url,
            len(objects),
        )
        return WorkflowResult(
            workflow="synthetic_data_generation",
            status="completed",
            connector=info,
            steps=[parse_step, build_step, execute_step],
            artifacts=artifacts,
            detail=(
                f"Generated synthetic ONE Record {intent['object_type']} "
                f"data via RecordForge ({len(objects)} object(s))."
                if objects
                else (
                    f"RecordForge accepted the request for "
                    f"{intent['count']} × {intent['object_type']}."
                )
            ),
        )


def get_recordforge_connector(settings: Settings | None = None) -> RecordForgeConnector:
    return RecordForgeConnector(settings=settings)
