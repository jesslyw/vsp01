import logging

class Logger:
    def __init__(self):
        logging.basicConfig(
            filename='logs/application.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger()

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    #def critical(self, message):
    #    self.logger.critical(message)