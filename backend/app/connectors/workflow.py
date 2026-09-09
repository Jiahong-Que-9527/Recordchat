"""Structured workflow result schema (#32).

Frontend can render these via ChatResponse.structured_output without parsing
prose. Discriminator field ``kind`` is always ``workflow_result``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.connectors.base import ConnectorAvailability


class WorkflowStep(BaseModel):
    id: str
    title: str
    status: Literal["pending", "ready", "skipped", "failed", "completed"]
    detail: str | None = None


class WorkflowArtifact(BaseModel):
    kind: str
    name: str
    content: dict[str, Any] | list[Any] | str | None = None


class WorkflowConnectorInfo(BaseModel):
    name: str
    availability: ConnectorAvailability
    base_url: str | None = None
    detail: str | None = None


class WorkflowResult(BaseModel):
    kind: Literal["workflow_result"] = "workflow_result"
    workflow: str
    status: Literal["planned", "blocked", "failed", "completed"]
    connector: WorkflowConnectorInfo
    steps: list[WorkflowStep] = Field(default_factory=list)
    artifacts: list[WorkflowArtifact] = Field(default_factory=list)
    detail: str | None = None

    def to_answer_text(self) -> str:
        """Human-readable summary kept in ChatResponse.answer."""
        lines = [
            f"Workflow: {self.workflow}",
            f"Status: {self.status}",
            f"Connector: {self.connector.name} ({self.connector.availability.value})",
        ]
        if self.detail:
            lines.append("")
            lines.append(self.detail)
        if self.steps:
            lines.append("")
            lines.append("Steps:")
            for step in self.steps:
                suffix = f" — {step.detail}" if step.detail else ""
                lines.append(f"- [{step.status}] {step.title}{suffix}")
        if self.artifacts:
            lines.append("")
            lines.append("Artifacts:")
            for art in self.artifacts:
                lines.append(f"- {art.name} ({art.kind})")
        lines.append("")
        lines.append("Implementation note:")
        if self.connector.availability == ConnectorAvailability.unconfigured:
            lines.append(
                "Set RECORDFORGE_URL (and optionally RECORDFORGE_API_KEY) to enable "
                "remote generation. Until then RecordChat returns a structured "
                "blocked workflow plan instead of calling an external service."
            )
        elif self.connector.availability == ConnectorAvailability.unavailable:
            lines.append(
                "The RecordForge connector is configured but could not complete "
                "the remote call. The structured workflow result captures the "
                "failure without crashing the assistant."
            )
        else:
            lines.append(
                "A structured generation plan is ready. Live HTTP execution against "
                "RecordForge lands in the next connector slice (#13); this response "
                "exposes the execution path and request artifact."
            )
        return "\n".join(lines)
