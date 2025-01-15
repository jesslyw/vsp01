import os
import socket


class Config:
    # Netzwerk- und API-Konfiguration
    STAR_PORT = 8121
    GALAXY_PORT = 8121
    IP = socket.gethostbyname(socket.gethostname())
    API_BASE_URL = "/vs/v1/system/"
    API_BASE_URL_STAR= "/vs/v1/star/"

    # UDP-Konfiguration
    TIMEOUT_LISTENING_FOR_UPD_RESPONSE = 5  # in Sekunden

    # Broadcast-Konfiguration
    BROADCAST_INTERVAL = 5  # Interval in Sekunden für Broadcasts
    BROADCAST_RETRY_ATTEMPTS = 2  # Anzahl der Widerholungen für HALLO?

    # Stern- und Komponenten-Konfiguration
    MAX_COMPONENTS = 4  # Maximale Anzahl an Komponenten in einem Stern
    UUID_MIN = 1000  # Mindestwert für UUID-Generierung
    UUID_MAX = 9999  # Maximalwert für UUID-Generierung

    # Status Update Konfiguration
    STATUS_UPDATE_INTERVAL = 30  # Intervall in Sekunden zwischen Statusmeldungen
    STATUS_UPDATE_RETRY_INTERVALS = [10, 20]  # Retry-Intervalle in Sekunden
    STATUS_UPDATE_MAX_ATTEMPTS = 3  # Maximale Wiederholungsversuche

    # Timeout-Konfiguration
    STATUS_UPDATE_TIMEOUT = 5  # Timeout für die HTTP-Requests in Sekunden

    # Exit-Request-Konfiguration
    EXIT_REQUEST_RETRIES = 2  # Anzahl der Wiederholungen für Exit-Requests
    # fmt: off
    EXIT_REQUEST_WAIT = [10, 20] # Wartezeit zwischen Exit-Request-Versuchen in Sekunden
    # fmt: on

    # Gesundheitsprüfung
    HEALTH_CHECK_INTERVAL = 30  # Intervall in Sekunden für die Gesundheitsprüfung
    PEER_INACTIVITY_THRESHOLD = 60  # Inaktivitätsgrenze in Sekunden

    # Abmeldeversuche
    UNREGISTER_RETRY_COUNT = 2  # Anzahl der Wiederholungen für Abmeldeversuche
    UNREGISTER_RETRY_DELAY = [10, 20]  # Verzögerung in Sekunden zwischen Wiederholungen

    # API-Felder
    STAR_UUID_FIELD = "star"
    SOL_UUID_FIELD = "sol"
    COMPONENT_UUID_FIELD = "component"
    COMPONENT_IP_FIELD = "com-ip"
    COMPONENT_TCP_FIELD = "com-tcp"
    STATUS_FIELD = "status"

    SOL_IP_FIELD = "sol-ip"
    SOL_TCP_FIELD = "sol-tcp"

    # Logging
    LOGGING_LEVEL = "INFO"

    # Exit-Konfiguration
    EXIT_CODE_SUCCESS = 0  # Successful exit
    EXIT_CODE_ERROR = 1  # Exit with error

    # Syslog logging (/var/log/syslog) anschalten (false für lokale Enwicklung)
    LOG_TO_SYSLOG = False
