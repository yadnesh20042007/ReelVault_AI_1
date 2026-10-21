import unittest
from unittest.mock import patch, MagicMock
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings
from app.services.auth_service import get_auth_service


class TestAuthEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        get_auth_service.cache_clear()
        get_settings.cache_clear()

    def tearDown(self):
        get_auth_service.cache_clear()
        get_settings.cache_clear()

    def test_protected_me_missing_bearer_token(self):
        """Calling /v1/auth/me without an Authorization header must return 401."""
        response = self.client.get("/v1/auth/me")
        self.assertEqual(response.status_code, 401)
        self.assertIn("missing bearer token", response.text.lower())

    def test_protected_me_invalid_token(self):
        """Calling /v1/auth/me with an invalid or fabricated bearer token must return 401."""
        response = self.client.get(
            "/v1/auth/me",
            headers={"Authorization": "Bearer invalid_fabricated_token_xyz"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("invalid or expired token", response.text.lower())

    def test_login_invalid_credentials(self):
        """Invalid credentials submitted to /v1/auth/login must be rejected with 401."""
        response = self.client.post(
            "/v1/auth/login",
            json={"email": "nonexistent_tester_12345@example.com", "password": "wrong_password_xyz"}
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data.get("error", {}).get("code"), "invalid_credentials")

    def test_mock_token_rejected_in_production(self):
        """In production, mock_static_admin_token must be rejected with 401."""
        with patch.object(get_settings(), "app_env", "production"):
            response = self.client.get(
                "/v1/auth/me",
                headers={"Authorization": "Bearer mock_static_admin_token"}
            )
            self.assertEqual(response.status_code, 401)
            self.assertIn("invalid or expired token", response.text.lower())

    def test_mock_login_rejected_in_production(self):
        """In production, admin/admin must NOT return a mock admin token and should hit Supabase."""
        with patch.object(get_settings(), "app_env", "production"):
            response = self.client.post(
                "/v1/auth/login",
                json={"email": "admin", "password": "admin"}
            )
            # In production, mock bypass is disabled, so it attempts Supabase and fails with 400/401/422
            self.assertNotEqual(response.status_code, 200)
            if response.status_code == 200:
                self.assertNotEqual(response.json().get("access_token"), "mock_static_admin_token")

    def test_mock_refresh_rejected_in_production(self):
        """In production, mock_static_admin_refresh_token must be rejected with 401."""
        with patch.object(get_settings(), "app_env", "production"):
            response = self.client.post(
                "/v1/auth/refresh",
                json={"refresh_token": "mock_static_admin_refresh_token"}
            )
            self.assertEqual(response.status_code, 401)

    def test_mock_admin_allowed_in_dev_mode(self):
        """In development mode, mock static admin credentials are functional for offline prototyping."""
        with patch.object(get_settings(), "app_env", "dev"):
            response = self.client.post(
                "/v1/auth/login",
                json={"email": "admin", "password": "admin"}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data.get("access_token"), "mock_static_admin_token")

            # Validate /v1/auth/me works in dev with mock token
            me_resp = self.client.get(
                "/v1/auth/me",
                headers={"Authorization": "Bearer mock_static_admin_token"}
            )
            self.assertEqual(me_resp.status_code, 200)
            self.assertEqual(me_resp.json().get("id"), "usr_static_admin")

    def test_login_success_with_genuine_supabase_response(self):
        """When Supabase returns a valid token payload, /v1/auth/login returns TokenOut."""
        fake_supabase_payload = {
            "access_token": "supabase_real_jwt_token_example",
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": "supabase_real_refresh_token_example",
            "user": {
                "id": "c906bad1-12bf-4de5-8a3c-ff77a82250fa",
                "email": "user@example.com",
            }
        }
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = fake_supabase_payload

        with patch("httpx.Client.post", return_value=mock_resp):
            response = self.client.post(
                "/v1/auth/login",
                json={"email": "user@example.com", "password": "CorrectPassword123!"}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["access_token"], "supabase_real_jwt_token_example")
            self.assertEqual(data["user"]["id"], "c906bad1-12bf-4de5-8a3c-ff77a82250fa")
            self.assertEqual(data["user"]["email"], "user@example.com")


if __name__ == "__main__":
    unittest.main()
