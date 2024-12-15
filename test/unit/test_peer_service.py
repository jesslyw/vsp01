import pytest
from unittest.mock import MagicMock, call, patch

import requests

from src.app.config import Config
from src.service.peer_service import PeerService
from src.service.sol_service import SolService


class TestPeerService:
    @pytest.fixture
    def mock_peer_service(self):
        # Mock für udp_service und logger
        udp_service = MagicMock()
        logger = MagicMock()
        component_model = MagicMock()
        # Initialisiere PeerService
        service = PeerService(udp_service)

        # Initialisiere SOLService innerhalb von PeerService
        service.sol_service = MagicMock()
        service.sol_service.star_uuid = "star-uuid"
        service.sol_service.sol_uuid = "sol-uuid"

        return service

    def test_broadcast_hello_and_initialize_with_valid_responses(self, mock_peer_service):
        """
        Test, ob die Methode bei gültigen SOL-Antworten korrekt funktioniert.
        """
        udp_service.listen_for_responses.return_value = [
            ({"star": "star-uuid", "sol": "sol-uuid", "sol-ip": "127.0.0.1", "sol-tcp": "8000"}, ("127.0.0.1", 8000))
        ]

        responses = mock_peer_service.broadcast_hello_and_initialize()

        # Assertions
        mock_peer_service.logger.info.assert_any_call("Broadcasting HELLO? to discover SOL...")
        mock_peer_service.logger.info.assert_any_call("Discovered 1 valid SOL component(s).")
        assert len(responses) == 1
        assert responses[0][0]["star"] == "star-uuid"

    def test_broadcast_hello_and_initialize_with_no_responses(self, mock_peer_service):
        """
        Test, ob die Methode sich selbst als SOL initialisiert, wenn keine Antworten eingehen.
        """
        mock_peer_service.udp_service.listen_for_responses.return_value = []

        responses = mock_peer_service.broadcast_hello_and_initialize()

        # Assertions
        mock_peer_service.logger.warning.assert_any_call(
            "No SOL components found after retries. Initializing as new SOL...")
        assert responses == []

    def test_broadcast_hello_and_initialize_with_invalid_responses(self, mock_peer_service):
        """
        Test, ob die Methode ungültige Antworten ignoriert.
        """
        mock_peer_service.udp_service.listen_for_responses.return_value = [
            ({"invalid": "data"}, ("127.0.0.1", 8000))
        ]

        responses = mock_peer_service.broadcast_hello_and_initialize()

        # Assertions
        mock_peer_service.logger.warning.assert_any_call(
            "Invalid SOL response from 127.0.0.1:8000: {'invalid': 'data'}")
        assert responses == []

    def test_broadcast_hello_and_initialize_with_retries(self, mock_peer_service):
        """
        Test, ob die Methode korrekt mehrmals versucht, Antworten zu erhalten.
        """
        mock_peer_service.udp_service.listen_for_responses.side_effect = [[], [], [
            ({"star": "star-uuid", "sol": "sol-uuid", "sol-ip": "127.0.0.1", "sol-tcp": "8000"}, ("127.0.0.1", 8000))
        ]]

        responses = mock_peer_service.broadcast_hello_and_initialize()

        # Assertions
        assert len(responses) == 1
        assert mock_peer_service.udp_service.listen_for_responses.call_count == 3
        mock_peer_service.logger.warning.assert_any_call("No responses received. Retrying... (1/2)")
        mock_peer_service.logger.warning.assert_any_call("No responses received. Retrying... (2/2)")

    def test_broadcast_hello_and_initialize_handles_exceptions(self, mock_peer_service):
        """
        Test, ob die Methode Exceptions beim Senden oder Empfangen behandelt.
        """
        mock_peer_service.udp_service.broadcast_udp_message.side_effect = Exception("Broadcast error")
        mock_peer_service.udp_service.listen_for_responses.side_effect = Exception("Listening error")

        responses = mock_peer_service.broadcast_hello_and_initialize()

        # Assertions
        mock_peer_service.logger.error.assert_any_call("Failed to broadcast HELLO?: Broadcast error")
        assert responses == []

    def test_choose_sol_empty_responses(self, mock_peer_service):
        """
        Test: Leere `valid_responses` sollte `(None, None)` zurückgeben.
        """
        valid_responses = []

        response, addr = mock_peer_service.choose_sol(valid_responses)

        assert response is None
        assert addr is None
        mock_peer_service.logger.warning.assert_called_once_with("Keine validen SOL-Komponenten verfügbar.")

    def test_choose_sol_single_response(self, mock_peer_service):
        """
        Test: Wenn `valid_responses` nur eine Antwort enthält, sollte diese gewählt werden.
        """
        valid_responses = [
            ({"sol": "1001", "star": "star1"}, ("192.168.1.1", 8000))
        ]

        response, addr = mock_peer_service.choose_sol(valid_responses)

        assert response == {"sol": "1001", "star": "star1"}
        assert addr == ("192.168.1.1", 8000)
        mock_peer_service.logger.info.assert_called_once_with(
            "Gewählter SOL: {'sol': '1001', 'star': 'star1'} von 192.168.1.1:8000")

    def test_choose_sol_multiple_responses(self, mock_peer_service):
        """
        Test: Wähle die Antwort mit der größten UUID aus mehreren Antworten.
        """
        valid_responses = [
            ({"sol": "1001", "star": "star1"}, ("192.168.1.1", 8000)),
            ({"sol": "1003", "star": "star2"}, ("192.168.1.2", 8001)),
            ({"sol": "1002", "star": "star3"}, ("192.168.1.3", 8002))
        ]

        response, addr = mock_peer_service.choose_sol(valid_responses)

        assert response == {"sol": "1003", "star": "star2"}
        assert addr == ("192.168.1.2", 8001)
        mock_peer_service.logger.info.assert_called_once_with(
            "Gewählter SOL: {'sol': '1003', 'star': 'star2'} von 192.168.1.2:8001")

    def test_initialize_as_sol(self, mock_peer_service):
        """
        Test, ob die Methode `initialize_as_sol` die Komponente korrekt als SOL initialisiert.
        """
        # Mock für die SOLService
        mock_sol_service = MagicMock()
        SolService.return_value = mock_sol_service

        # Die Methode ausführen
        mock_peer_service.initialize_as_sol()

        # Überprüfen, ob SOLService korrekt erstellt wurde
        mock_sol_service = mock_peer_service.sol_service
        assert isinstance(mock_sol_service, SolService)
        assert mock_sol_service.star_uuid is not None
        assert mock_sol_service.sol_uuid is not None
        assert mock_sol_service.registered_peers[0]["component"] == mock_sol_service.sol_uuid
        assert mock_sol_service.registered_peers[0]["com-ip"] == mock_peer_service.udp_service.ip
        assert mock_sol_service.registered_peers[0]["com-tcp"] == mock_peer_service.udp_service.port

        # Überprüfen, ob der Logger die korrekten Meldungen ausgibt
        mock_peer_service.logger.info.assert_any_call(
            f"Initializing as new SOL with STAR-UUID: {mock_sol_service.star_uuid}, COM-UUID: {mock_sol_service.sol_uuid}"
        )
        mock_peer_service.logger.info.assert_any_call(
            f"Self-registered as SOL with STAR-UUID: {mock_sol_service.star_uuid}"
        )

    @patch("requests.patch")
    def test_send_status_update_successful(self, mock_patch, mock_peer_service):
        """
        Test: Erfolgreiches Senden eines Statusupdates.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        result = mock_peer_service.send_status_update("127.0.0.1", 9000)

        # Assertions
        assert result is True
        mock_patch.assert_called_once_with(
            "http://127.0.0.1:9000/vs/v1/system/sol-uuid",
            json={
                "star": "star-uuid",
                "sol": "sol-uuid",
                "component": "sol-uuid",
                "com-ip": "127.0.0.1",
                "com-tcp": 8000,
                "status": 200,
            },
        )
        mock_peer_service.logger.info.assert_any_call("Status update successful.")

    @patch("requests.patch")
    def test_send_status_update_failure(self, mock_patch, mock_peer_service):
        """
        Test: Fehlerhafte Antwort während des Statusupdates.
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_patch.return_value = mock_response

        result = mock_peer_service.send_status_update("127.0.0.1", 9000)

        # Assertions
        assert result is False
        assert mock_patch.call_count == Config.STATUS_UPDATE_RETRIES + 1
        mock_peer_service.logger.warning.assert_any_call(
            "Status update failed: 500 Internal Server Error"
        )

    @patch("requests.patch")
    def test_send_status_update_exception(self, mock_patch, mock_peer_service):
        """
        Test: Ausnahme während des Sendevorgangs.
        """
        mock_patch.side_effect = requests.RequestException("Network error")

        result = mock_peer_service.send_status_update("127.0.0.1", 9000)

        # Assertions
        assert result is False
        assert mock_patch.call_count == Config.STATUS_UPDATE_RETRIES + 1
        mock_peer_service.logger.error.assert_any_call("Error sending status update: Network error")

    @patch("requests.patch")
    def test_send_status_update_retry_logic(self, mock_patch, mock_peer_service):
        """
        Test: Überprüfung der Retry-Logik bei fehlerhaften Antworten.
        """
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_patch.return_value = mock_response

        result = mock_peer_service.send_status_update("127.0.0.1", 9000)

        # Assertions
        assert result is False
        assert mock_patch.call_count == Config.STATUS_UPDATE_RETRIES + 1
        mock_peer_service.logger.warning.assert_any_call("Retrying status update... (2/3)")

    @patch("requests.delete")
    def test_send_exit_request_successful(self, mock_delete, mock_peer_service):
        """
        Test: Erfolgreiches Senden einer EXIT-Anforderung.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        result = mock_peer_service.send_exit_request("127.0.0.1", 9000)

        # Assertions
        assert result is True
        mock_delete.assert_called_once_with(
            "http://127.0.0.1:9000/vs/v1/system/sol-uuid?sol=star-uuid"
        )
        mock_peer_service.logger.info.assert_any_call("Component successfully unregistered from SOL.")

    @patch("requests.delete")
    def test_send_exit_request_unauthorized(self, mock_delete, mock_peer_service):
        """
        Test: Antwort mit Statuscode 401 (Unauthorized).
        """
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_delete.return_value = mock_response

        result = mock_peer_service.send_exit_request("127.0.0.1", 9000)

        # Assertions
        assert result is False
        assert mock_delete.call_count == 1
        mock_peer_service.logger.warning.assert_any_call("Unauthorized to unregister from SOL. Exiting with error.")

    @patch("requests.delete")
    def test_send_exit_request_not_found(self, mock_delete, mock_peer_service):
        """
        Test: Antwort mit Statuscode 404 (Not Found).
        """
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_delete.return_value = mock_response

        result = mock_peer_service.send_exit_request("127.0.0.1", 9000)

        # Assertions
        assert result is False
        assert mock_delete.call_count == 1
        mock_peer_service.logger.warning.assert_any_call("Component not found in SOL. Exiting with error.")

    @patch("requests.delete")
    def test_send_exit_request_unexpected_response(self, mock_delete, mock_peer_service):
        """
        Test: Antwort mit unerwartetem Statuscode.
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_delete.return_value = mock_response

        result = mock_peer_service.send_exit_request("127.0.0.1", 9000)

        # Assertions
        assert result is False
        assert mock_delete.call_count == Config.EXIT_REQUEST_RETRIES
        mock_peer_service.logger.warning.assert_any_call(
            "Unexpected response: 500 Internal Server Error"
        )

    @patch("requests.delete")
    def test_send_exit_request_exception(self, mock_delete, mock_peer_service):
        """
        Test: Ausnahme während des Sendevorgangs.
        """
        mock_delete.side_effect = requests.RequestException("Network error")

        result = mock_peer_service.send_exit_request("127.0.0.1", 9000)

        # Assertions
        assert result is False
        assert mock_delete.call_count == Config.EXIT_REQUEST_RETRIES
        mock_peer_service.logger.error.assert_any_call("Error sending EXIT request: Network error")

    @patch("requests.delete")
    def test_send_exit_request_retry_logic(self, mock_delete, mock_peer_service):
        """
        Test: Überprüfung der Retry-Logik bei fehlerhaften Antworten.
        """
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_delete.return_value = mock_response

        result = mock_peer_service.send_exit_request("127.0.0.1", 9000)

        # Assertions
        assert result is False
        assert mock_delete.call_count == Config.EXIT_REQUEST_RETRIES
        mock_peer_service.logger.warning.assert_any_call("Retrying EXIT request... (1/3)")
        mock_peer_service.logger.warning.assert_any_call("Retrying EXIT request... (2/3)")
        mock_peer_service.logger.warning.assert_any_call("Retrying EXIT request... (3/3)")