import logging
from os import environ

class Formatter(logging.Formatter):

    reset = '\x1b[0m'

    gray = '\x1b[1;30m'
    red = '\x1b[31m'
    bold_red = '\x1b[31;1m'
    green = '\x1b[32m'
    yellow = '\x1b[33m'
    blue = '\x1b[34m'


    def gen_template(self, color):
        return logging.Formatter(
            '%(asctime)s' + self.gray + ': ' + self.reset + '%(threadName)-11s' + self.gray + '[' + color + '%(levelname)s' + self.gray + ']' + self.reset + ' %(filename)s' + self.gray + ':' + self.reset+'%(lineno)d' + self.gray + ' » ' + self.reset + '%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.FORMATS =  {
            logging.DEBUG: self.gen_template(self.green),
            logging.INFO: self.gen_template(self.blue),
            logging.WARNING: self.gen_template(self.yellow),
            logging.ERROR: self.gen_template(self.red),
            logging.CRITICAL: self.gen_template(self.bold_red)
        }

    def format(self, record):
        return self.FORMATS[record.levelno].format(record)

logger = logging.getLogger()

handler = logging.StreamHandler()
handler.setFormatter(Formatter())

logger.addHandler(handler)
logger.setLevel(logging._nameToLevel[environ.get('LOG_LEVEL', 'DEBUG')])