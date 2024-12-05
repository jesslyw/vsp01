from datetime import datetime
import logging
import logging.handlers
import sys
from src.app.config import Config

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
    def __init__(self, com_uuid):

        # create the logger
        self.logger = logging.getLogger()

        # set the log level 
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(process)d - %(com_uuid)s: %(message)s')
        
        # file handler - logs will be written to the 'logs' directory
        file_handler = logging.FileHandler(f'src/logs/application_{datetime.now().strftime("%Y-%m-%d")}.log', mode="a")
        file_handler.setFormatter(formatter)

        # stream handler (console output)
        console_handler = logging.StreamHandler(sys.stdout)  
        console_handler.setFormatter(formatter)
        
        # by default, logs will be written to the host system's log files unless 
        # a remote ip and port is provided 
        if Config.LOG_TO_SYSLOG:
            # syslog handler 
            syslog_handler = logging.handlers.SysLogHandler(address=("localhost", 514))
            syslog_handler.setFormatter(formatter)
            self.logger.addHandler(syslog_handler)
        
        # add handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # store the component_uuid for future use in the log context
        self.com_uuid = com_uuid


    def info(self, message):
                self.logger.info(message, extra={'com_uuid': self.com_uuid})

    def error(self, message):
                self.logger.error(message, extra={'com_uuid': self.com_uuid})

    def warning(self, message):
                self.logger.warning(message, extra={'com_uuid': self.com_uuid})

