import pytest
from unittest.mock import patch
from io import BytesIO

from app import upload_file


class TestPostRequestsHandler:
    """Tests for upload_file route"""

    def test_upload_file_success(self, client, api_key, valid_image_data):
        # Use mock or a temporary file to simulate an upload
        with patch("app.handle_upload", return_value=True):
            response = client.post(
                "/media/images/test.jpg",
                headers={"Authorization": api_key},
                data={"file": (BytesIO(valid_image_data), "test.jpg")},
            )
            assert response.status_code == 200

    @patch("app.handle_upload", return_value=False)
    def test_upload_file_failure(
        self, mock_handle_upload, client, api_key, valid_image_data
    ):
        headers = {"Authorization": api_key}
        data = {"file": (BytesIO(valid_image_data), "test.jpg")}

        response = client.post("/media/images/test.jpg", headers=headers, data=data)
        assert response.status_code == 501
