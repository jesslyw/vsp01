import logging

class Logger:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('src/logs/application.log'),  # Log to file
                logging.StreamHandler()  # Log to console
            ]
        )
        self.logger = logging.getLogger()

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)
