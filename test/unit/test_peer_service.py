import pytest
from unittest.mock import MagicMock

from src.service.peer_service import PeerService


class TestPeerService:
    def test_broadcast_hello_no_responses(self, mocker):
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

    def test_broadcast_hello_valid_responses(self, mocker):
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

    def test_broadcast_hello_mixed_responses(self, mocker):
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

    def test_choose_sol_no_responses(self, mocker):
        # Arrange
        logger_mock = mocker.MagicMock()
        service = PeerService(udp_service=None, component_model=None, logger=logger_mock)

        # Act
        response, addr = service.choose_sol([])

        # Assert
        assert response is None
        assert addr is None
        logger_mock.warning.assert_called_once_with("Keine validen SOL-Komponenten verfügbar.")

    def test_choose_sol_one_response(self, mocker):
        # Arrange
        logger_mock = mocker.MagicMock()
        valid_response = {"sol": "abc123", "star": "star1", "sol-ip": "192.168.1.1", "sol-tcp": 8013}
        service = PeerService(udp_service=None, component_model=None, logger=logger_mock)

        # Act
        response, addr = service.choose_sol([(valid_response, ("192.168.1.1", 8013))])

        # Assert
        assert response == valid_response
        assert addr == ("192.168.1.1", 8013)
        logger_mock.info.assert_called_once_with(f"Gewählter SOL: {valid_response} von 192.168.1.1:8013")

    def test_choose_sol_multiple_responses(self, mocker):
        # Arrange
        logger_mock = mocker.MagicMock()
        valid_responses = [
            ({"sol": "abc123", "star": "star1", "sol-ip": "192.168.1.1", "sol-tcp": 8013}, ("192.168.1.1", 8013)),
            ({"sol": "def456", "star": "star2", "sol-ip": "192.168.1.2", "sol-tcp": 8013}, ("192.168.1.2", 8013)),
            ({"sol": "xyz789", "star": "star3", "sol-ip": "192.168.1.3", "sol-tcp": 8013}, ("192.168.1.3", 8013)),
        ]
        service = PeerService(udp_service=None, component_model=None, logger=logger_mock)

        # Act
        response, addr = service.choose_sol(valid_responses)

        # Assert
        assert response["sol"] == "xyz789"
        assert addr == ("192.168.1.3", 8013)
        logger_mock.info.assert_called_once_with(
            f"Gewählter SOL: {response} von {addr[0]}:{addr[1]}"
        )

    def test_choose_sol_duplicate_uuids(self, mocker):
        # Arrange
        logger_mock = mocker.MagicMock()
        valid_responses = [
            ({"sol": "abc123", "star": "star1", "sol-ip": "192.168.1.1", "sol-tcp": 8013}, ("192.168.1.1", 8013)),
            ({"sol": "abc123", "star": "star2", "sol-ip": "192.168.1.2", "sol-tcp": 8013}, ("192.168.1.2", 8013)),
        ]
        service = PeerService(udp_service=None, component_model=None, logger=logger_mock)

        # Act
        response, addr = service.choose_sol(valid_responses)

        # Assert
        assert response["sol"] == "abc123"
        assert addr == ("192.168.1.1", 8013)
        logger_mock.info.assert_called_once_with(
            f"Gewählter SOL: {response} von {addr[0]}:{addr[1]}"
        )

