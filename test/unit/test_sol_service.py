import pytest
from unittest.mock import MagicMock
from src.service.sol_service import SOLService


def test_listen_for_hello_and_respond(mocker):
    # Arrange
    udp_service_mock = mocker.MagicMock()
    logger_mock = mocker.MagicMock()

    star_uuid = "star-123"
    sol_uuid = "sol-456"
    ip = "192.168.1.100"
    star_port = 8000

    sol_service = SOLService(
        udp_service=udp_service_mock,
        component_model=None,
        logger=logger_mock,
        star_uuid=star_uuid,
        sol_uuid=sol_uuid,
        ip=ip,
        star_port=star_port
    )

    message = "HELLO?"
    sender_addr = ("192.168.1.200", 5000)

    # Simuliere die Callback-Methode
    def mock_callback(msg, addr):
        assert msg == message
        assert addr == sender_addr
        sol_service.send_response(addr[0], addr[1])

    udp_service_mock.listen.side_effect = lambda port, callback: mock_callback(message, sender_addr)

    # Act
    sol_service.listen_for_hello()

    # Assert
    udp_service_mock.send_response.assert_called_once_with(
        {
            "star": star_uuid,
            "sol": sol_uuid,
            "sol-ip": ip,
            "sol-tcp": star_port,
            "component": sol_uuid,
        },
        sender_addr[0],
        sender_addr[1],
    )
    logger_mock.info.assert_any_call(f"Sending response to {sender_addr[0]}:{sender_addr[1]}: "
                                      f"{{'star': '{star_uuid}', 'sol': '{sol_uuid}', 'sol-ip': '{ip}', "
                                      f"'sol-tcp': {star_port}, 'component': '{sol_uuid}'}}")
