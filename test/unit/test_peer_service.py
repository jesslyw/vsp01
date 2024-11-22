import pytest
from unittest.mock import MagicMock

from src.service.peer_service import PeerService


def test_broadcast_hello_no_responses(mocker):
    # Arrange
    udp_service_mock = mocker.MagicMock()
    logger_mock = mocker.MagicMock()
    component_model_mock = mocker.MagicMock()  # Mock für component_model

    udp_service_mock.listen_for_responses.return_value = []  # Simuliere keine Antworten

    # Übergabe des Mock-Objekts für component_model
    service = PeerService(udp_service=udp_service_mock, logger=logger_mock, component_model=component_model_mock)

    # Act
    responses = service.broadcast_hello()

    # Assert
    assert responses == []
    logger_mock.info.assert_any_call("Broadcasting HELLO? to discover SOL...")
    logger_mock.warning.assert_called_with("No SOL components discovered.")


def test_broadcast_hello_valid_responses(mocker):
    # Arrange
    udp_service_mock = mocker.MagicMock()
    logger_mock = mocker.MagicMock()
    component_model_mock = mocker.MagicMock()

    valid_response = {"star": "abc123", "sol": "def456", "sol-ip": "192.168.1.1", "sol-tcp": 8013}
    udp_service_mock.listen_for_responses.return_value = [(valid_response, ("192.168.1.1", 8013))]

    # Übergabe des Mock-Objekts für component_model
    service = PeerService(udp_service=udp_service_mock, logger=logger_mock, component_model=component_model_mock)

    # Act
    responses = service.broadcast_hello()

    # Assert
    assert responses == [(valid_response, ("192.168.1.1", 8013))]
    logger_mock.info.assert_any_call(
        f"Discovered SOL: {valid_response} from 192.168.1.1:8013"
    )


def test_broadcast_hello_mixed_responses(mocker):
    # Arrange
    udp_service_mock = mocker.MagicMock()
    logger_mock = mocker.MagicMock()
    component_model_mock = mocker.MagicMock()
    valid_response = {"star": "abc123", "sol": "def456", "sol-ip": "192.168.1.1", "sol-tcp": 8013}
    invalid_response = {"unknown": "invalid"}
    udp_service_mock.listen_for_responses.return_value = [
        (valid_response, ("192.168.1.1", 8013)),
        (invalid_response, ("192.168.1.2", 8013))
    ]

    service = PeerService(udp_service=udp_service_mock, logger=logger_mock, component_model=component_model_mock)

    # Act
    responses = service.broadcast_hello()

    # Assert
    assert responses == [(valid_response, ("192.168.1.1", 8013))]
    logger_mock.warning.assert_called_with("Invalid SOL response from 192.168.1.2:8013: {'unknown': 'invalid'}")
