import pytest
from app import create_app
import os


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["MEDIA_FILES_DEST"] = "media"
    return app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def api_key():
    return os.getenv("API_KEY")


@pytest.fixture(scope="function")
def valid_image_data():
    return b"89 PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


@pytest.fixture(scope="function")
def invalid_image_data():
    return b"This is not an image file"


@pytest.fixture(scope="function")
def media_files_destination(app):
    return app.config["MEDIA_FILES_DEST"]
