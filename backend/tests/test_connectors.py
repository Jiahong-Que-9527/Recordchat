from app.connectors.base import Connector, ConnectorAvailability
from app.core.config import Settings


class _DummyConnector(Connector):
    def __init__(self, base_url: str | None) -> None:
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def base_url(self) -> str | None:
        return self._base_url


def test_connector_describe_unconfigured_without_base_url():
    descriptor = _DummyConnector(base_url="").describe()

    assert descriptor.name == "dummy"
    assert descriptor.availability == ConnectorAvailability.unconfigured
    assert descriptor.configured is False
    assert "disabled" in (descriptor.detail or "")


def test_connector_describe_ready_when_base_url_present():
    descriptor = _DummyConnector(base_url="https://recordforge.example.com").describe()

    assert descriptor.availability == ConnectorAvailability.ready
    assert descriptor.configured is True
    assert descriptor.base_url == "https://recordforge.example.com"


def test_settings_expose_recordforge_config():
    settings = Settings(
        recordforge_url="https://recordforge.example.com",
        recordforge_api_key="secret",
    )

    assert settings.recordforge_url == "https://recordforge.example.com"
    assert settings.recordforge_api_key == "secret"
