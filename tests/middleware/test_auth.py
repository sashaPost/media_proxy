import pytest
from middleware.auth import check_api_key
from unittest.mock import patch


class TestCheckApiKey:
    @pytest.fixture
    def setup(self, app):
        @app.before_request
        @check_api_key
        def before_request():
            pass

    def test_valid_api_key(self, client, api_key):
        response = client.post(
            "/media/images/test.jpg", headers={"Authorization": api_key}, data={}
        )
        assert response.status_code != 401

    def test_invalid_api_key(self, client):
        response = client.post(
            "/media/images/test.jpg",
            headers={"Authorization": "invalid_api_key"},
            data={},
        )
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized"}

    def test_missing_api_key(self, client):
        response = client.post("/media/images/test.jpg", data={})
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized"}

    def test_empty_api_key(self, client):
        response = client.post(
            "/media/images/test.jpg", headers={"Authorization": ""}, data={}
        )
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized"}

    @pytest.mark.parametrize("header", ["X-API-Key", "Api-Key", "Token"])
    def test_incorrect_header_name(self, client, api_key, header):
        response = client.post(
            "/media/images/test.jpg", headers={header: api_key}, data={}
        )
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized"}

    def test_case_sensitive_api_key(self, client, api_key):
        response = client.post(
            "/media/images/test.jpg",
            headers={"Authorization": api_key.swapcase()},
            data={},
        )
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized"}

    def test_whitespace_in_api_key(self, client, api_key):
        response = client.post(
            "/media/images/test.jpg", headers={"Authorization": f" {api_key} "}, data={}
        )
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized"}
