import pytest
from unittest.mock import MagicMock
from ontologytimemachine.pac.generator import build_pac


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.host = "127.0.0.1"
    config.port = 8898
    config.restrictedAccess = False
    config.archivoDomains = ["dbpedia.org", "w3.org"]
    return config


def test_build_pac_normal_mode(mock_config):
    mock_config.restrictedAccess = False

    pac_content = build_pac(mock_config)

    assert 'return "PROXY 127.0.0.1:8898";' in pac_content
    assert "archivoDomains" not in pac_content


def test_build_pac_restricted_mode(mock_config):
    mock_config.restrictedAccess = True
    mock_config.archivoDomains = ["dbpedia.org", "w3.org"]

    pac_content = build_pac(mock_config)

    assert "var archivoDomains =" in pac_content
    assert '"dbpedia.org": true' in pac_content
    assert '"w3.org": true' in pac_content
    assert "function isOntologyHost" in pac_content
    assert 'return "PROXY 127.0.0.1:8898";' in pac_content
    assert 'return "DIRECT";' in pac_content


def test_build_pac_handles_any_interface_host(mock_config):
    mock_config.host = ["0.0.0.0", "::"]  # Емуляція масиву інтерфейсів
    mock_config.restrictedAccess = False

    pac_content = build_pac(mock_config)

    # Браузер має отримати саме 127.0.0.1
    assert 'return "PROXY 127.0.0.1:8898";' in pac_content
    assert "0.0.0.0" not in pac_content