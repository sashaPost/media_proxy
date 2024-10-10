import unittest
from flask import Flask
from middleware.auth import create_auth_middleware


class MockConfig:
    def __init__(self, api_key):
        self.API_KEY = api_key


class TestAuthMiddleware(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.client = self.app.test_client()

    def test_valid_api_key(self):
        config = MockConfig("valid_key")
        auth = create_auth_middleware(config)

        @self.app.route("/test")
        @auth.check_api_key
        def test_route():
            return "Success", 200

        response = self.client.get("/test", headers={"Authorization": "valid_key"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "Success")

    def test_invalid_api_key(self):
        config = MockConfig("valid_key")
        auth = create_auth_middleware(config)

        @self.app.route("/test")
        @auth.check_api_key
        def test_route():
            return "Success", 200

        response = self.client.get("/test", headers={"Authorization": "invalid_key"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Unauthorized", response.json["error"])

    def test_missing_api_key(self):
        config = MockConfig("valid_key")
        auth = create_auth_middleware(config)

        @self.app.route("/test")
        @auth.check_api_key
        def test_route():
            return "Success", 200

        response = self.client.get("/test")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Unauthorized", response.json["error"])


if __name__ == "__main__":
    unittest.main()
