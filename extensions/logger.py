import logging
from flask import current_app


class Logger:
    def __init__(self, app=None):
        # self.logger = None
        self.logger = logging.getLogger(__name__)
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.logger = app.logger
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def info(self, msg):
        if self.app:
            self.app.logger.info(msg)
        else:
            self.logger.info(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)


logger = Logger()

# with app.app_context():
#     logger.init_app(current_app)
