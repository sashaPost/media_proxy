import pytest
from unittest.mock import patch, MagicMock, mock_open
from flask import Response
from utils.upload_handler import handle_upload
import io


class TestHandleUpload:
    @pytest.fixture
    def mock_request(self):
        with patch("flask.request") as mock_request:
            yield mock_request

    @pytest.fixture
    def mock_open(self):
        with patch("builtins.open", mock_open=True) as mock_file:
            yield mock_file

    @pytest.fixture
    def mock_os(self):
        with patch("os.chmod") as mock_chmod:
            yield mock_chmod

    def test_no_file_in_request(self, app):
        with app.test_request_context("/upload", method="POST"):
            response = handle_upload("images/test.jpg")
            assert response.status_code == 400
            assert response.data == b"No file part"

    def test_empty_filename(self, app):
        with app.test_request_context(
            "/upload", method="POST", data={"image": (io.BytesIO(b"test data"), "")}
        ):
            response = handle_upload("images/")
            assert response.status_code == 400
            assert response.data == b"Empty filename"

    def test_allowed_path_and_extension_fails(self, app):
        with app.test_request_context(
            "/upload",
            method="POST",
            data={"image": (io.BytesIO(b"test data"), "test.jpg")},
        ):
            with patch(
                "utils.path_utils.allowed_path_and_extension", return_value=False
            ):
                result = handle_upload("images/test.jpg")
                assert result is False

    def test_succesfull_upload(self, app, mock_open, mock_os):
        with app.test_request_context(
            "/upload",
            method="POST",
            data={"image": (io.BytesIO(b"test data"), "test.jpg")},
        ):
            with patch(
                "utils.path_utils.allowed_path_and_extension", return_value=True
            ), patch(
                "utils.path_utils.path_secure", return_value="/media/images/test.jpg"
            ):
                result = handle_upload("images/test.jpg")
                assert result is True
