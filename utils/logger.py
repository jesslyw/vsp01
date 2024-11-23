import logging

class Logger:
    '''
    logs messages to the console and log file
    using either info() or error() determines the severity level of the message recorded 
    '''
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s', # log format
            handlers=[
                logging.FileHandler('logs/application.log'),  # log to file
                logging.StreamHandler()  # log to console
            ]
        )
        self.logger = logging.getLogger()

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)
