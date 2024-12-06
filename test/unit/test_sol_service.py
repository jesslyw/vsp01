from datetime import datetime, timedelta

import pytest
from unittest.mock import MagicMock, patch

import requests

from src.app.config import Config
from src.service.sol_service import SOLService


class TestSOLService:
    @pytest.fixture
    def mock_sol_service(self):
        udp_service = MagicMock()
        logger = MagicMock()
        sol_service = SOLService(
            udp_service=udp_service,
            peer=MagicMock(),
            logger=logger,
            star_uuid="test-star-uuid",
            sol_uuid="test-sol-uuid",
            ip="127.0.0.1",
            star_port=8000,
        )
        sol_service.registered_peers = [
            {"component": "peer1", "com-ip": "192.168.1.1", "com-tcp": 9000, "status": "active"},
            {"component": "peer2", "com-ip": "192.168.1.2", "com-tcp": 9001, "status": "active"},
        ]
        return sol_service

    def test_listen_for_hello_valid_message(self, mock_sol_service):
        """
        Test: Handle a valid `HELLO?` message.
        """
        # Mock the send_response method
        mock_sol_service.send_response = MagicMock()

        # Simulate the callback behavior
        message = "HELLO?"
        addr = ("192.168.1.1", 9000)
        callback = mock_sol_service.udp_service.listen.call_args[1]["callback"]

        # Call the callback directly
        callback(message, addr)

        # Assertions
        mock_sol_service.logger.info.assert_any_call(f"Received HELLO? from {addr[0]}:{addr[1]}")
        mock_sol_service.send_response.assert_called_once_with(addr[0], addr[1])

    def test_listen_for_hello_invalid_message(self, mock_sol_service):
        """
        Test: Handle an invalid message.
        """
        # Mock the send_response method
        mock_sol_service.send_response = MagicMock()

        # Simulate the callback behavior
        message = "INVALID_MESSAGE"
        addr = ("192.168.1.2", 9001)
        callback = mock_sol_service.udp_service.listen.call_args[1]["callback"]

        # Call the callback directly
        callback(message, addr)

        # Assertions
        mock_sol_service.logger.warning.assert_any_call(
            f"Unexpected message from {addr[0]}:{addr[1]}: {message}"
        )
        mock_sol_service.send_response.assert_not_called()

    @patch("threading.Thread")
    def test_listen_for_hello_exception_handling(self, mock_thread, mock_sol_service):
        """
        Test: Handle an exception during message handling.
        """
        # Mock the UDP service to raise an exception
        mock_sol_service.udp_service.listen.side_effect = Exception("Test exception")

        # Run the method
        mock_sol_service.listen_for_hello()

        # Assertions
        mock_sol_service.logger.error.assert_called_once_with(
            "Error while listening for HELLO? messages: Test exception"
        )

    def test_send_response_successful(self, mock_sol_service):
        """
        Test: Successfully sending a response.
        """
        # Arrange
        target_ip = "192.168.1.1"
        target_port = 9000

        # Act
        mock_sol_service.send_response(target_ip, target_port)

        # Assert
        expected_response = {
            "star": "test-star-uuid",
            "sol": "test-sol-uuid",
            "sol-ip": "127.0.0.1",
            "sol-tcp": 8000,
            "component": "test-sol-uuid",
        }
        mock_sol_service.udp_service.send_response.assert_called_once_with(
            expected_response, target_ip, target_port
        )
        mock_sol_service.logger.info.assert_any_call(
            f"Sending response to {target_ip}:{target_port}: {expected_response}"
        )

    def test_send_response_exception_handling(self, mock_sol_service):
        """
        Test: Handle exception when sending a response.
        """
        # Arrange
        target_ip = "192.168.1.1"
        target_port = 9000
        mock_sol_service.udp_service.send_response.side_effect = Exception("Test exception")

        # Act
        mock_sol_service.send_response(target_ip, target_port)

        # Assert
        mock_sol_service.udp_service.send_response.assert_called_once()
        mock_sol_service.logger.error.assert_called_once_with(
            f"Failed to send response to {target_ip}:{target_port}: Test exception"
        )


    @patch("requests.delete")
    def test_unregister_all_peers_success(self, mock_delete, mock_sol_service):
        """
        Test: Successfully unregister all peers.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        # Act
        with pytest.raises(SystemExit) as e:
            mock_sol_service.unregister_all_peers_and_exit()

        # Assert
        assert e.value.code == Config.SOL_EXIT_CODE
        assert mock_delete.call_count == len(mock_sol_service.registered_peers)
        for peer in mock_sol_service.registered_peers:
            mock_delete.assert_any_call(
                f"http://{peer['com-ip']}:{peer['com-tcp']}/vs/v1/system/{peer['component']}?sol={mock_sol_service.star_uuid}"
            )
        mock_sol_service.logger.info.assert_any_call("All peers processed. Exiting SOL...")

    @patch("requests.delete")
    def test_unregister_peer_unauthorized(self, mock_delete, mock_sol_service):
        """
        Test: Handle unauthorized unregistration (401 response).
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_delete.return_value = mock_response

        # Act
        with pytest.raises(SystemExit) as e:
            mock_sol_service.unregister_all_peers_and_exit()

        # Assert
        assert e.value.code == Config.SOL_EXIT_CODE
        for peer in mock_sol_service.registered_peers:
            mock_sol_service.logger.warning.assert_any_call(
                f"Unauthorized attempt to unregister peer {peer['component']}. Skipping."
            )

    @patch("requests.delete")
    def test_unregister_peer_unexpected_response(self, mock_delete, mock_sol_service):
        """
        Test: Handle unexpected response codes during unregistration.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_delete.return_value = mock_response

        # Act
        with pytest.raises(SystemExit) as e:
            mock_sol_service.unregister_all_peers_and_exit()

        # Assert
        assert e.value.code == Config.SOL_EXIT_CODE
        for peer in mock_sol_service.registered_peers:
            mock_sol_service.logger.warning.assert_any_call(
                f"Unexpected response from peer {peer['component']}: 500"
            )

    @patch("requests.delete")
    def test_unregister_peer_request_exception(self, mock_delete, mock_sol_service):
        """
        Test: Handle request exception during unregistration.
        """
        # Arrange
        mock_delete.side_effect = requests.RequestException("Network error")

        # Act
        with pytest.raises(SystemExit) as e:
            mock_sol_service.unregister_all_peers_and_exit()

        # Assert
        assert e.value.code == Config.SOL_EXIT_CODE
        for peer in mock_sol_service.registered_peers:
            mock_sol_service.logger.error.assert_any_call(
                f"Failed to contact peer {peer['component']}: Network error"
            )

    @patch("requests.delete")
    @patch("time.sleep", return_value=None)  # Avoid delay
    def test_unregister_peer_retry_logic(self, mock_sleep, mock_delete, mock_sol_service):
        """
        Test: Ensure retry logic is followed for unregistration.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_delete.return_value = mock_response

        # Act
        with pytest.raises(SystemExit) as e:
            mock_sol_service.unregister_all_peers_and_exit()

        # Assert
        assert e.value.code == Config.SOL_EXIT_CODE
        assert mock_delete.call_count == len(mock_sol_service.registered_peers) * Config.UNREGISTER_RETRY_COUNT
        for peer in mock_sol_service.registered_peers:
            mock_sol_service.logger.warning.assert_any_call(
                f"Retrying DELETE request to peer {peer['component']}... ({Config.UNREGISTER_RETRY_COUNT}/{Config.UNREGISTER_RETRY_COUNT})"
            )