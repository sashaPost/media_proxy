# !!! NOT BEING EXECUTED, SHOULDN'T WORK AS EXPECTED

import pytest
from flask import Flask
from routes.setup_routes import directories_check, setup_bp
import os
from unittest.mock import patch, call


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["MEDIA_FILES_DEST"] = "/tmp/test_media"
    app.config["ALLOWED_DIRECTORIES"] = ["images", "files"]
    app.register_blueprint(setup_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


class DirectoriesCheck:
    @patch("setup_routes.os.makedirs")
    @patch("setup_routes.logger")
    def test_directories_check_success(self, mock_logger, mock_makedirs, app, client):
        client.get("/")

        # mock_makedirs.assert_any_call('/tmp/test_media', exist_ok=True)
        # mock_makedirs.assert_any_call('/tmp/test_media/images', exist_ok=True)
        # mock_makedirs.assert_any_call('/tmp/test_media/files', exist_ok=True)

        expected_calls = [
            call("/tmp/test_media", exist_ok=True),
            call("/tmp/test_media/images", exist_ok=True),
            call("/tmp/test_media/files", exist_ok=True),
        ]
        mock_makedirs.assert_has_calls(expected_calls, any_order=True)

        mock_logger.assert_called_with("*** 'directories_check' was triggered ***")

    @patch("setup_routes.os.makedirs")
    @patch("setup_routes.logger")
    def test_directories_check_oserror(self, mock_logger, mock_makedirs, app, client):
        mock_makedirs.side_effect = OSError("Test error")
        client.get("/")
        mock_logger.error.assert_called_with(
            "Failed to create directory /tmp/test_media: Test error"
        )

    def test_blueprint_resistered(self, app):
        assert "setup" in app.blueprints
        assert app.blueprints["setup"] == setup_bp
