import pytest
from app import create_app
import os
import tempfile
import shutil


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "MEDIA_FILES_DEST": tempfile.mkdtemp(),
        }
    )
    yield app
    # Clean up the temporary directory after tests
    shutil.rmtree(app.config["MEDIA_FILES_DEST"])


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def api_key():
    key = os.getenv("API_KEY")
    if not key:
        pytest.skip("API_KEY environment variable not set")
    return key


@pytest.fixture(scope="function")
def valid_image_data():
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xfa\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xcc\x59\xe7\x00\x00\x00\x00IEND\xaeB`\x82"


@pytest.fixture(scope="function")
def invalid_image_data():
    return b"This is not an image file"


@pytest.fixture(scope="function")
def media_files_destination(app):
    return app.config["MEDIA_FILES_DEST"]


@pytest.fixture(scope="function")
def cleanup_media_files(app):
    yield
    for filename in os.listdir(app.config["MEDIA_FILES_DEST"]):
        file_path = os.path.join(app.config["MEDIA_FILES_DEST"], filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)


@pytest.fixture(scope="function")
def mock_file(tmp_path):
    file = tmp_path / "test_file.txt"
    file.write_text("This is a test file")
    return file


@pytest.fixture(scope="function")
def app_with_context(app):
    with app.app_context():
        yield app
