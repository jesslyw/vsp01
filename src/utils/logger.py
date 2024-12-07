from datetime import datetime
import logging
import logging.handlers
import sys
from app.config import Config


class Logger:
    '''
    A custom logging utility for a component with optional syslog (system) logging
    The log format includes the timestamp, log level, process ID, and the com UUID
    Log messages will be stored in the 'src/logs/application_{date}.log' file

    Usage:
    To use the Logger, create an instance of the Logger class and call the appropriate methods:
    - info(message)
    - error(message)
    - warning(message)

    '''

    _instance = None  # Singleton instance

    def __new__(cls):
        # create the logger
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)

            # Create the logger
            cls._instance.logger = logging.getLogger("GlobalLogger")
            cls._instance.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(process)d: %(message)s')

        # file handler - logs will be written to the 'logs' directory
        file_handler = logging.FileHandler(f'logs/application_{datetime.now().strftime("%Y-%m-%d")}.log', mode="a")
        file_handler.setFormatter(formatter)

        # stream handler (console output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        cls._instance.logger.addHandler(file_handler)
        cls._instance.logger.addHandler(console_handler)

        # by default, logs will be written to the host system's log files unless
        # a remote ip and port is provided
        if Config.LOG_TO_SYSLOG:
            # syslog handler
            syslog_handler = logging.handlers.SysLogHandler(address=("localhost", 514))
            syslog_handler.setFormatter(formatter)
            cls._instance.logger.addHandler(syslog_handler)

            # store the component_uuid for future use in the log context
            # Store the component UUID
            # cls._instance.com_uuid = com_uuid or "GLOBAL" ?
        return cls._instance

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)


# Module-level global logger
global_logger = Logger()
