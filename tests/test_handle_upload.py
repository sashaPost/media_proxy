import pytest
from unittest.mock import patch
import unittest.mock as mock
from app import handle_upload


class TestHandleUpload:
    """Tests for 'handle_upload'"""

    @patch("app.is_valid_image")
    def test_handle_upload_valid(
        self, mock_is_valid_image, client, api_key
    ):  # No need for patching
        mock_is_valid_image.return_value = True

        origin_file_path = "images/test.jpg"

        # Open the image directly
        with open("tests/test.jpg", "rb") as f:
            file_data = f.read()

            response = client.post(
                "media/images/test.jpg",
                data={"file": f},
                headers={"Authorization": api_key},
            )
        assert response.status_code == 200  # Or your expected success code

    @patch("app.allowed_path_and_extension")
    @patch("app.path_secure")
    @patch("builtins.open")
    def test_handle_upload_save_error(
        self, mock_open, mock_path_secure, mock_allowed_path_and_extension
    ):
        origin_file_path = "images/test.jpg"
        mock_allowed_path_and_extension.return_value = True
        mock_path_secure.return_value = "media/images/test.jpg"

        mock_file = mock.MagicMock()
        mock_file.stream.tell.return_value = 4096

        mock_request = mock.MagicMock()
        mock_request.files = {"image": mock_file}

        mock_open.side_effect = IOError("Simulated file saving error")

        result = handle_upload(origin_file_path)
        assert result is False

    @patch("app.allowed_path_and_extension")
    def test_handle_upload_invalid_extension(self, mock_allowed_path_and_extension):
        origin_file_path = "images/data.csv"
        mock_allowed_path_and_extension.return_value = False

        result = handle_upload(origin_file_path)
        assert result is False

    @patch("app.allowed_path_and_extension")
    @patch("app.is_valid_image")
    def test_handle_upload_empty_filename(
        self, mock_allowed_path_and_extension, mock_is_valid_image
    ):
        origin_file_path = "images/test.jpg"
        mock_allowed_path_and_extension.return_value = True
        mock_is_valid_image.return_value = True

        mock_file = mock.MagicMock()
        mock_file.stream.tell.return_value = 4096
        mock_file.filename = ""
        mock_request = mock.MagicMock()
        mock_request.files = {"image": mock_file}

        result = handle_upload(origin_file_path)
        assert result == False

    def test_handle_upload_no_file(self):
        mock_request = mock.MagicMock()
        mock_request.files = {}

        result = handle_upload("test.jpg")
        assert result is False
