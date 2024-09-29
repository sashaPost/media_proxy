from flask import Flask
from config import Config
from extensions.logger import logger
from routes.file_routes import file_bp
from routes.setup_routes import setup_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    logger.init_app(app)

    app.register_blueprint(setup_bp)
    # setup_bp = Blueprint("setup", __name__)
    #
    # @setup_bp.before_app_request
    # directories_check()
    app.register_blueprint(file_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
