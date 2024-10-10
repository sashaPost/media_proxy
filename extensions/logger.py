import inspect
import logging
import os


class Logger:
    def __init__(self, app=None):
        self.logger = logging.getLogger(__name__)
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.logger = app.logger
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(caller_file)s:%(caller_line)d - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _log(self, level, msg):
        # Get the caller's frame
        current_frame = inspect.currentframe()
        caller_frame = current_frame.f_back

        # Find the first frame that is not in this file
        while caller_frame.f_code.co_filename == __file__:
            caller_frame = caller_frame.f_back

        # Extract filename and line number
        filename = os.path.basename(caller_frame.f_code.co_filename)
        lineno = caller_frame.f_lineno

        # Create a dictionary with extra fields
        extra = {"caller_file": filename, "caller_line": lineno}

        # Log the message with extra info
        if self.app:
            getattr(self.app.logger, level)(msg, extra=extra)
        else:
            getattr(self.logger, level)(msg, extra=extra)

    def info(self, msg):
        self._log("info", msg)

    def debug(self, msg):
        self._log("debug", msg)

    def warning(self, msg):
        self._log("warning", msg)

    def error(self, msg):
        self._log("error", msg)


logger = Logger()
