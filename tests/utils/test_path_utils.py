import io
from flask import current_app, Response
from PIL import Image
import pytest
from unittest.mock import patch
from utils.path_utils import (
    get_file_extension,
    get_request_directory,
    is_valid_file_path,
    path_secure,
)


class TestGetFileExtension:
    def test_valid_extension(self, app):
        with app.app_context():
            with patch("flask.current_app") as mock_app:
                mock_app.config = current_app.config["ALLOWED_EXTENSIONS"]
                assert get_file_extension("test_image.jpg") is True

    def test_invalid_extension(self, app):
        with app.app_context():
            with patch("flask.current_app") as mock_app:
                mock_app.config = current_app.config["ALLOWED_EXTENSIONS"]
                assert get_file_extension("test_image.exe") is False


class TestGetRequestDirectory:
    def test_get_request_directory(self, app):
        req_abs_file_path = "/path/to/file.txt"
        result = get_request_directory(req_abs_file_path)
        assert result == "/path/to"


class TestIsValidFilePath:
    @pytest.fixture
    def mock_os(self, app):
        with app.app_context():
            with patch("flask.current_app") as mock_exists, patch(
                "os.path.abspath"
            ) as mock_abspath:
                mock_exists.return_value = True
                mock_abspath.side_effect = lambda x: x
                yield mock_exists, mock_abspath

    def test_valid_file_path(self, app, mock_os):
        with app.app_context():
            app.config["MEDIA_FILES_DEST"] = "media/"
            app.config["ALLOWED_DIRECTORIES"] = ["images", "files"]
            assert is_valid_file_path("images/test.jpg") is True

    def test_invalid_file_path(self, app, mock_os):
        with app.app_context():
            app.config["MEDIA_FILES_DEST"] = "media/"
            app.config["ALLOWED_DIRECTORIES"] = ["images", "files"]
            assert is_valid_file_path("homiki/test.jpg") is False


class TestPathSecure:
    @pytest.fixture
    def mock_request(self):
        with patch("werkzeug.utils.secure_filename") as mock_secure_filename:
            yield mock_secure_filename

    def test_valid_image_path_secure(self, app, mock_request):
        # Create a small valid JPEG image
        img = Image.new("RGB", (60, 30), color="red")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()

        # Use Flask's test_request_context to simulate the HTTP request and 'request.files'
        with app.test_request_context(
            "/upload",
            method="POST",
            data={"image": (io.BytesIO(img_byte_arr), "test.jpg")},
        ):
            app.config["MEDIA_FILES_DEST"] = "media/"
            result = path_secure("images/test.jpg", "image")
            assert result == "media/images/test.jpg"

    def test_invalid_image_path_secure(self, app, mock_request):
        # Create a small valid JPEG image
        img = Image.new("RGB", (60, 30), color="red")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()

        # Test case 1: Invalid destination directory
        with app.test_request_context(
            "/upload",
            method="POST",
            data={"image": (io.BytesIO(img_byte_arr), "test.jpg")},
        ):
            app.config["MEDIA_FILES_DEST"] = "media/"
            result = path_secure("invalid-dir/test.jpg", "image")
            assert isinstance(result, Response)
            assert result.status_code == 403

        # Test case 2: Invalid file type (not an image)
        with app.test_request_context(
            "/upload",
            method="POST",
            data={"image": (io.BytesIO(b"This is not an image"), "test.jpg")},
        ):
            app.config["MEDIA_FILES_DEST"] = "media/"
            result = path_secure("images/test.jpg", "image")
            assert result is False

        # Test case 3: Missing file
        with app.test_request_context("/upload", method="POST", data={}):
            app.config["MEDIA_FILES_DEST"] = "media/"
            with pytest.raises(KeyError):
                path_secure("images/missing.jpg", "image")
