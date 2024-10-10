from flask import Flask
from config.app_config import AppConfig
from extensions.logger import logger
from routes.file_routes import file_bp
from routes.health_check import health_bp
from routes.setup_routes import setup_bp
import os


def create_app(config_class=AppConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    logger.init_app(app)

    app.register_blueprint(file_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(setup_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host=host, port=port)
