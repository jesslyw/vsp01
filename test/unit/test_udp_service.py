import pytest

from service.communication.udp_service import UdpService


def test_broadcast_message(mocker):
    # Arrange
    mock_socket = mocker.patch("socket.socket")
    udp_service = UdpService()

    # Act
    udp_service.broadcast_message(8013, "Test message")

    # Assert
    mock_socket.assert_called_once()
    # Weitere Assertions für die Nachricht oder das Verhalten hinzufügen