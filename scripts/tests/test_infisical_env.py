import importlib.util
import json
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib import error as urllib_error

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = REPO_ROOT / "scripts" / "infisical_env.py"
    spec = importlib.util.spec_from_file_location("infisical_env", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, payload: object, status: int = 200):
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args) -> bool:
        return False


class InfisicalEnvTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_fetch_secrets_with_token_injects_missing_keys_only(self):
        calls: list[str] = []

        def fake_urlopen(req, timeout=30, context=None):
            del timeout, context
            calls.append(req.full_url)
            self.assertEqual(req.get_header("Authorization"), "Bearer st.example")
            return FakeResponse(
                {
                    "secrets": [
                        {"secretName": "OPENAI_API_KEY", "secretValue": "from-infisical"},
                        {"secretName": "DATABASE_URL", "secretValue": "should-not-win"},
                    ]
                }
            )

        with mock.patch.object(self.mod.urllib_request, "urlopen", side_effect=fake_urlopen):
            merged = self.mod.build_injected_env(
                {
                    "INFISICAL_TOKEN": "st.example",
                    "INFISICAL_API_URL": "https://infisical.example",
                    "INFISICAL_PROJECT_ID": "proj-1",
                    "INFISICAL_ENV": "dev",
                    "DATABASE_URL": "postgres://local",
                }
            )

        self.assertEqual(merged["OPENAI_API_KEY"], "from-infisical")
        self.assertEqual(merged["DATABASE_URL"], "postgres://local")
        self.assertIn("viewSecretValue=true", calls[0])
        self.assertIn("projectId=proj-1", calls[0])

    def test_universal_auth_then_list_secrets(self):
        calls: list[tuple[str, str]] = []

        def fake_urlopen(req, timeout=30, context=None):
            del timeout, context
            method = req.get_method()
            calls.append((method, req.full_url))
            if req.full_url.endswith("/api/v1/auth/universal-auth/login"):
                return FakeResponse({"accessToken": "jwt-token", "expiresIn": 3600})
            self.assertEqual(req.get_header("Authorization"), "Bearer jwt-token")
            return FakeResponse({"secrets": [{"secretKey": "REDIS_URL", "secretValue": "redis://secret"}]})

        with mock.patch.object(self.mod.urllib_request, "urlopen", side_effect=fake_urlopen):
            merged = self.mod.build_injected_env(
                {
                    "INFISICAL_CLIENT_ID": "client",
                    "INFISICAL_CLIENT_SECRET": "secret",
                    "INFISICAL_API_URL": "https://infisical.example",
                    "INFISICAL_PROJECT_ID": "proj-1",
                }
            )

        self.assertEqual(merged["REDIS_URL"], "redis://secret")
        self.assertEqual(calls[0][0], "POST")
        self.assertIn("/api/v4/secrets", calls[1][1])

    def test_missing_project_id_fails(self):
        with self.assertRaises(self.mod.InfisicalEnvError) as raised:
            self.mod.build_injected_env(
                {
                    "INFISICAL_TOKEN": "st.example",
                    "INFISICAL_API_URL": "https://infisical.example",
                }
            )
        self.assertIn("INFISICAL_PROJECT_ID", str(raised.exception))

    def test_pass_through_without_auth(self):
        env = {"DATABASE_URL": "postgres://local", "INFISICAL_API_URL": "https://infisical.example"}
        self.assertEqual(self.mod.build_injected_env(env)["DATABASE_URL"], "postgres://local")

    def test_tls_error_is_visible(self):
        def fake_urlopen(req, timeout=30, context=None):
            del req, timeout, context
            raise urllib_error.URLError(ssl.SSLCertVerificationError("certificate has expired"))

        with mock.patch.object(self.mod.urllib_request, "urlopen", side_effect=fake_urlopen):
            with self.assertRaises(self.mod.InfisicalEnvError) as raised:
                self.mod.build_injected_env(
                    {
                        "INFISICAL_TOKEN": "st.example",
                        "INFISICAL_API_URL": "https://infisical.example",
                        "INFISICAL_PROJECT_ID": "proj-1",
                    }
                )
        self.assertIn("TLS", str(raised.exception))
        self.assertIn("infisical.example", str(raised.exception))

    def test_load_repo_env_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "infisical.defaults.env").write_text(
                "INFISICAL_API_URL=https://defaults.example\nINFISICAL_PROJECT_ID=from-defaults\n",
                encoding="utf-8",
            )
            (root / ".env").write_text("INFISICAL_TOKEN=from-env\n", encoding="utf-8")
            loaded = self.mod.load_repo_env_files(root)
        self.assertEqual(loaded["INFISICAL_API_URL"], "https://defaults.example")
        self.assertEqual(loaded["INFISICAL_TOKEN"], "from-env")
        self.assertEqual(loaded["INFISICAL_PROJECT_ID"], "from-defaults")


if __name__ == "__main__":
    unittest.main()
