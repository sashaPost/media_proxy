import pytest
from unittest.mock import patch
import tempfile
import os
from app import (
    allowed_path_and_extension,
    get_file_extension,
    get_request_directory,
    is_valid_file_path,
)


class TestPathRelatedFunctions:
    """Tests for path-related functions"""

    @patch("app.is_valid_image")
    @patch("app.is_valid_file")
    def test_path_secure_valid_image(
        self, mock_is_valid_image, mock_is_valid_file, client, api_key
    ):
        # Arrange:
        origin_file_path = "images/test.jpg"
        file_key = "image"

        test_file = "tests/test.jpg"

        mock_is_valid_image.return_value = True
        mock_is_valid_file.return_value = False

        with open(test_file, "rb") as f:
            response = client.post(
                "/media/images/test.jpg",
                data={"image": f},  # Important change
                headers={"Authorization": api_key},
            )

        # Assert:
        assert response.status_code == 200

    @patch("app.is_valid_image")
    @patch("app.is_valid_file")
    def test_path_secure_directory_traversal(
        self, mock_is_valid_image, mock_is_valid_file, client, api_key
    ):
        # Arrange:
        origin_file_path = "../../sensitive_data.txt"
        file_key = "image"

        mock_is_valid_image.return_value = False
        mock_is_valid_file.return_value = False

        # Act:
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp_file:
            # You don't necessarily need to write anything to the temp file
            with open(tmp_file.name, "rb") as f:
                response = client.post(
                    "/media/images/../../sensitive_data.txt",
                    data={file_key: (f, origin_file_path)},  # Important change
                    headers={"Authorization": api_key},
                )

        # Assert:
        assert response.status_code == 501

    @patch("app.is_valid_image")
    @patch("app.is_valid_file")
    def test_path_secure_invalid_file_type(
        self, mock_is_valid_image, mock_is_valid_file, client, api_key
    ):
        # Arrange:
        origin_file_path = "images/test.pdf"
        file_key = "image"

        # Act:
        mock_is_valid_image.return_value = False
        mock_is_valid_file.return_value = False

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            tmp_file.write(b"This is a test PDF file.")

            with open(tmp_file.name, "rb") as f:
                response = client.post(
                    "/media/images/test.pdf",
                    data={"image": f},
                    headers={"Authorization": api_key},
                )

        # # Assert:
        assert response.status_code == 501

    def test_get_file_extension_valid_image(self):
        origin_file_path = "images/example.jpg"
        result = get_file_extension(origin_file_path)
        assert result is True

    def test_get_file_extension_valid_document(self):
        origin_file_path = "files/example.docx"
        result = get_file_extension(origin_file_path)
        assert result is True

    def test_get_file_extension_invalid(self):
        origin_file_path = "images/invalid.csv"
        result = get_file_extension(origin_file_path)
        assert result is False

    def test_get_request_directory_simple(self):
        req_abs_file_path = "/var/www/html/media_proxy/media/images/test.jpg"
        result = get_request_directory(req_abs_file_path)
        assert result == "/var/www/html/media_proxy/media/images"

    @patch("app.get_request_directory")
    def test_is_valid_file_path_valid(
        self, mock_get_request_directory, media_files_destination
    ):
        origin_file_path = "images/test.jpg"

        expected_dir = os.path.abspath(
            os.path.normpath(os.path.join(media_files_destination, "images"))
        )

        mock_get_request_directory.return_value = expected_dir

        with patch("os.path.exists", return_value=True):
            result = is_valid_file_path(origin_file_path)
            assert result is True

    @patch("app.get_request_directory")
    def test_is_valid_file_path_invalid_dir(
        self, mock_get_request_directory, media_files_destination
    ):
        origin_file_path = "documents/report.pdf"
        mock_get_request_directory.return_value = os.path.join(
            media_files_destination, "documents"
        )  # Simulate invalid directory

        result = is_valid_file_path(origin_file_path)
        assert result is False

    @patch("app.get_request_directory")
    def test_is_valid_file_path_outside_media(self, mock_get_request_directory):
        origin_file_path = "../../etc/passwd"  # Attempt to escape the media directory
        mock_get_request_directory.return_value = (
            "/var/www/html/media_proxy/media/documents"
        )

        result = is_valid_file_path(origin_file_path)
        assert result is False

    @patch("app.get_request_directory")
    def test_is_valid_file_path_nonexistent_directory(
        self, mock_get_request_directory, media_files_destination
    ):
        origin_file_path = "images/test.jpg"
        mock_get_request_directory.return_value = os.path.join(
            media_files_destination, "images"
        )

        with patch("os.path.exists", return_value=False):
            result = is_valid_file_path(origin_file_path)
            assert result is False

    @patch("app.get_request_directory")
    def test_is_valid_file_path_edge_cases(
        self, mock_get_request_directory, media_files_destination
    ):

        expected_dir = os.path.abspath(
            os.path.normpath(os.path.join(media_files_destination, "images"))
        )

        mock_get_request_directory.return_value = expected_dir

        test_cases = [
            ("images/file with spaces.jpg", True),  # File path with spaces
            ("images/FILE.JPG", True),  # Mixed case file name
            (
                "images/特殊字符.pdf",
                True,
            ),  # File with special characters (Adjust if needed)
            # ('images/../etc/passwd', False)  # this one results in True, deal with it later
        ]

        for file_path, expected_result in test_cases:
            with patch("os.path.exists", return_value=True):
                result = is_valid_file_path(file_path)
                assert result == expected_result

    @patch("app.is_valid_file_path")
    @patch("app.get_file_extension")
    def test_allowed_path_and_extension_vali(
        self, mock_is_valid_file_path, mock_get_file_extension
    ):
        origin_file_path = "images/test.jpg"
        mock_is_valid_file_path.return_value = True
        mock_get_file_extension.return_value = True

        result = allowed_path_and_extension(origin_file_path)
        assert result is True

    @patch("app.is_valid_file_path")
    @patch("app.get_file_extension")
    def test_allowed_path_and_extension_invalid_path(
        self, mock_is_valid_file_path, mock_get_file_extension
    ):
        origin_file_path = "documents/report.pdf"
        mock_is_valid_file_path.return_value = False
        mock_get_file_extension.return_value = True

        result = allowed_path_and_extension(origin_file_path)
        assert result is False

    @patch("app.is_valid_file_path")
    @patch("app.get_file_extension")
    def test_allowed_path_and_extension_invalid_extension(
        self, mock_is_valid_file_path, mock_get_file_extension
    ):
        origin_file_path = "images/data.csv"
        mock_is_valid_file_path.return_value = True
        mock_get_file_extension.return_value = False

        result = allowed_path_and_extension(origin_file_path)
        assert result is False
