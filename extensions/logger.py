import logging


class Logger:
    def __init__(self, app=None):
        self.logger = None
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


logger = Logger()
