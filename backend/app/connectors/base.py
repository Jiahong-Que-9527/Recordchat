"""Connector seam for external ecosystem tools.

Workflow orchestration should depend on this abstraction instead of binding the
RAG pipeline directly to RecordForge or other external services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectorAvailability(str, Enum):
    ready = "ready"
    unconfigured = "unconfigured"
    unavailable = "unavailable"


@dataclass(slots=True)
class ConnectorDescriptor:
    name: str
    availability: ConnectorAvailability
    base_url: str | None = None
    detail: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.base_url)


class Connector(ABC):
    """Base contract for optional external workflow connectors."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def base_url(self) -> str | None: ...

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def describe(self) -> ConnectorDescriptor:
        if not self.is_configured():
            return ConnectorDescriptor(
                name=self.name,
                availability=ConnectorAvailability.unconfigured,
                base_url=None,
                detail=(
                    f"{self.name} connector is disabled because its base URL is not configured."
                ),
            )

        return ConnectorDescriptor(
            name=self.name,
            availability=ConnectorAvailability.ready,
            base_url=self.base_url,
            detail=f"{self.name} connector is configured and available for orchestration.",
        )

    def unavailable_result(self, reason: str | None = None) -> ConnectorDescriptor:
        detail = reason or f"{self.name} connector could not complete the requested action."
        logger.warning("%s unavailable: %s", self.name, detail)
        return ConnectorDescriptor(
            name=self.name,
            availability=ConnectorAvailability.unavailable,
            base_url=self.base_url,
            detail=detail,
        )
