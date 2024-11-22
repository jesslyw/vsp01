import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.service.peer_service import PeerService
from src.service.sol_service import SOLService


class TestPeerService:
    def setup_method(self):
        """Setup for each test case."""
        self.udp_service_mock = MagicMock()
        self.component_model_mock = MagicMock()
        self.logger_mock = MagicMock()
        self.peer_service = PeerService(
            udp_service=self.udp_service_mock,
            component_model=self.component_model_mock,
            logger=self.logger_mock
        )

    def test_broadcast_hello_and_initialize_no_responses(self, mocker):
        """Test that SOL is initialized when no responses are received."""
        mocker.patch("time.sleep", return_value=None)  # Patch sleep for faster tests
        self.udp_service_mock.listen_for_responses.return_value = []

        # Act
        self.peer_service.broadcast_hello_and_initialize(retries=1, wait_time=1, max_components=4)

        # Assert
        self.logger_mock.warning.assert_any_call("No SOL components found after retries. Initializing as new SOL...")
        assert isinstance(self.peer_service.sol_service, SOLService)
        assert len(self.peer_service.sol_service.registered_components) == 1

        # Prüfe die Logger-Nachricht mit dem generierten STAR-UUID
        registered_message_calls = [
            call for call in self.logger_mock.info.call_args_list if "Self-registered as SOL with STAR-UUID:" in call[0][0]
        ]
        assert len(registered_message_calls) == 1  # Eine solche Nachricht sollte vorhanden sein

    def test_broadcast_hello_and_initialize_valid_responses(self):
        """Test that valid responses are handled correctly."""
        valid_response = {"star": "star-123", "sol": "sol-456", "sol-ip": "192.168.1.100", "sol-tcp": 8000}
        self.udp_service_mock.listen_for_responses.return_value = [(valid_response, ("192.168.1.100", 8000))]

        # Act
        responses = self.peer_service.broadcast_hello_and_initialize(retries=1, wait_time=1)

        # Assert
        assert len(responses) == 1
        self.logger_mock.info.assert_any_call("Discovered SOL: {'star': 'star-123', 'sol': 'sol-456', 'sol-ip': '192.168.1.100', 'sol-tcp': 8000} from 192.168.1.100:8000")

    def test_choose_sol_with_valid_responses(self):
        """Test choosing a SOL with valid responses."""
        valid_responses = [
            ({"star": "star-123", "sol": "sol-456", "sol-ip": "192.168.1.1", "sol-tcp": 8000}, ("192.168.1.1", 8000)),
            ({"star": "star-456", "sol": "sol-789", "sol-ip": "192.168.1.2", "sol-tcp": 8000}, ("192.168.1.2", 8000)),
        ]

        # Act
        chosen_response, chosen_addr = self.peer_service.choose_sol(valid_responses)

        # Assert
        assert chosen_response["sol"] == "sol-789"
        assert chosen_addr == ("192.168.1.2", 8000)
        expected_log = f"Gewählter SOL: {chosen_response} von {chosen_addr[0]}:{chosen_addr[1]}"
        self.logger_mock.info.assert_any_call(expected_log)

    def test_choose_sol_no_responses(self):
        """Test choosing a SOL when no valid responses exist."""
        # Act
        response, addr = self.peer_service.choose_sol([])

        # Assert
        assert response is None
        assert addr is None
        self.logger_mock.warning.assert_called_once_with("Keine validen SOL-Komponenten verfügbar.")

    def test_initialize_as_sol(self, mocker):
        """Test initialization as SOL."""
        mocker.patch("src.service.peer_service.datetime", wraps=datetime)
        datetime_mock = mocker.patch("src.service.peer_service.datetime.now")
        datetime_mock.return_value = datetime(2024, 1, 1, 12, 0, 0)

        # Act
        self.peer_service.initialize_as_sol(max_components=4)

        # Assert
        assert isinstance(self.peer_service.sol_service, SOLService)
        assert len(self.peer_service.sol_service.registered_components) == 1

        # Überprüfen der Logger-Nachricht
        self.logger_mock.info.assert_any_call(
            mocker.ANY)  # Sicherstellen, dass eine Logger-Nachricht protokolliert wurde

        # Suche nach der relevanten Logger-Meldung
        relevant_call = [
            call for call in self.logger_mock.info.call_args_list if
            "Self-registered as SOL with STAR-UUID:" in call[0][0]
        ]
        assert len(relevant_call) == 1  # Sicherstellen, dass die Nachricht genau einmal vorkommt

        # Überprüfen, dass die UUID korrekt generiert und geloggt wurde
        logged_message = relevant_call[0][0][0]
        assert logged_message.startswith("Self-registered as SOL with STAR-UUID: ")
        assert len(logged_message.split(": ")[1]) == 32  # UUID sollte 32 Zeichen lang sein (MD5-Hash)

    def test_generate_com_uuid_unique(self):
        """Test that COM-UUIDs are generated uniquely."""
        # Simulate existing components
        self.peer_service.sol_service = MagicMock()
        self.peer_service.sol_service.registered_components = [{"component": "1234"}]

        # Act
        uuid = self.peer_service.generate_com_uuid()

        # Assert
        assert uuid != "1234"
        assert 1000 <= uuid <= 9999

    def test_generate_star_uuid(self):
        """Test generation of STAR-UUID."""
        com_uuid = "4567"
        self.udp_service_mock.ip = "192.168.1.100"

        # Act
        star_uuid = self.peer_service.generate_star_uuid(com_uuid)

        # Assert
        assert len(star_uuid) == 32  # MD5 hashes are 32 characters long
        self.logger_mock.info.assert_not_called()  # Ensure no unnecessary logs
