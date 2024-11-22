class Config:
    # Netzwerk- und API-Konfiguration
    STAR_PORT = 8000
    PEER_PORT = 9000
    API_BASE_URL = "/vs/v1/system/"

    #UDP-Konfiguration
    TIMEOUT_LISTENING_FOR_UPD_RESPONSE= 5 # in Sekunden

    # Broadcast-Konfiguration
    BROADCAST_INTERVAL = 5  # Interval in Sekunden für Broadcasts

    # Stern- und Komponenten-Konfiguration
    MAX_COMPONENTS = 4  # Maximale Anzahl an Komponenten in einem Stern
    UUID_MIN = 1000  # Mindestwert für UUID-Generierung
    UUID_MAX = 9999  # Maximalwert für UUID-Generierung

    # Statusupdate-Konfiguration
    STATUS_UPDATE_RETRIES = 2  # Anzahl der Wiederholungen für Statusupdates
    STATUS_UPDATE_WAIT = 10  # Wartezeit zwischen Statusupdate-Versuchen in Sekunden

    # Exit-Request-Konfiguration
    EXIT_REQUEST_RETRIES = 3  # Anzahl der Wiederholungen für Exit-Requests
    EXIT_REQUEST_WAIT = 10  # Wartezeit zwischen Exit-Request-Versuchen in Sekunden

    # Gesundheitsprüfung
    HEALTH_CHECK_INTERVAL = 30  # Intervall in Sekunden für die Gesundheitsprüfung
    PEER_INACTIVITY_THRESHOLD = 60  # Inaktivitätsgrenze in Sekunden

    # Abmeldeversuche
    UNREGISTER_RETRY_COUNT = 2  # Anzahl der Wiederholungen für Abmeldeversuche
    UNREGISTER_RETRY_DELAY = 10  # Verzögerung in Sekunden zwischen Wiederholungen

    # API-Felder
    STAR_UUID_FIELD = "star"
    SOL_UUID_FIELD = "sol"
    COMPONENT_UUID_FIELD = "component"
    COMPONENT_IP_FIELD = "com-ip"
    COMPONENT_TCP_FIELD = "com-tcp"
    STATUS_FIELD = "status"

    # Logging
    LOGGING_LEVEL = "INFO"

    # Exit-Konfiguration
    SOL_EXIT_CODE = 0  # Exit-Code für SOL
