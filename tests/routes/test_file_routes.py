import pytest
from flask import Flask
from routes.file_routes import handle_get_request, handle_upload, file_bp
from unittest.mock import patch, MagicMock
import os


class TestFileRoutes:
    @patch("routes.file_routes.send_from_directory")
    def test_handle_get_request_success(self, mock_send, client):
        mock_send.return_value = "File content"
        response = client.get("/media/images/test.jpg")
        assert response.status_code == 200
        assert response.data == b"File content"
        mock_send.assert_called_once_with("media/images", "test.jpg")

    @patch("routes.file_routes.send_from_directory")
    def handle_get_request_file_not_found(self, mock_send, client):
        mock_send.side_effect = FileNotFoundError()
        response = client.get("/media/images/nonexistent.jpg")
        assert response.status_code == 404
        assert response.data == b"File not found"

    @patch("routes.file_routes.handle_upload")
    def test_upload_file_success(self, mock_handle_upload, client, api_key):
        mock_handle_upload.return_value = True
        response = client.post(
            "/media/images/test.jpg", headers={"Authorization": api_key}
        )
        assert response.status_code == 200
        # assert response.data == b'OK'
        assert response.json == {"message": "OK"}
        # mock_handle_upload.assert_called_once_with('images/test.jpg')

    @patch("routes.file_routes.handle_upload")
    def test_upload_file_failure(self, mock_handle_upload, client, api_key):
        mock_handle_upload.return_value = False
        response = client.post(
            "/media/images/test.jpg", headers={"Authorization": api_key}
        )
        assert response.status_code == 501
        # assert response.json == b'Error uploading file'
        assert response.json == {"error": "Error uploading file"}

    def test_upload_file_no_api_key(self, client):
        response = client.post("/media/images/test.jpg")
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized"}

    def test_upload_file_invalid_api_key(self, client):
        response = client.post(
            "/media/images/test.jpg", headers={"Authorization": "invalid_api_key"}
        )
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized"}
