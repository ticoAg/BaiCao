import importlib.util
import ssl
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = REPO_ROOT / "scripts" / "infisical_env.py"
    spec = importlib.util.spec_from_file_location("infisical_env", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class _Secret:
    def __init__(self, key: str, value: str):
        self.secretKey = key
        self.secretValue = value


class _Listed:
    def __init__(self, secrets: list[_Secret]):
        self.secrets = secrets
        self.imports = []


class _SecretsApi:
    def __init__(self, secrets: list[_Secret]):
        self._secrets = secrets
        self.kwargs: dict | None = None

    def list_secrets(self, **kwargs):
        self.kwargs = kwargs
        return _Listed(self._secrets)


class _UniversalAuth:
    def __init__(self):
        self.logged: list[tuple[str, str]] = []

    def login(self, client_id: str, client_secret: str):
        self.logged.append((client_id, client_secret))


class _Auth:
    def __init__(self):
        self.universal_auth = _UniversalAuth()


class FakeClient:
    def __init__(self, host: str, token: str | None = None, cache_ttl: int = 60):
        self.host = host
        self.token = token
        self.cache_ttl = cache_ttl
        self.auth = _Auth()
        self.secrets = _SecretsApi([_Secret("OPENAI_API_KEY", "from-sdk")])
        self.closed = False

    def close(self) -> None:
        self.closed = True


class InfisicalEnvTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_token_client_injects_missing_keys_only(self):
        created: list[FakeClient] = []

        def factory(**kwargs):
            client = FakeClient(**kwargs)
            created.append(client)
            return client

        merged = self.mod.build_injected_env(
            {
                "INFISICAL_TOKEN": "st.example",
                "INFISICAL_API_URL": "https://app.infisical.com",
                "INFISICAL_PROJECT_ID": "proj-1",
                "INFISICAL_ENV": "dev",
                "INFISICAL_SECRET_PATH": "/baicao",
                "DATABASE_URL": "postgres://local",
            },
            client_factory=factory,
        )

        self.assertEqual(merged["OPENAI_API_KEY"], "from-sdk")
        self.assertEqual(merged["DATABASE_URL"], "postgres://local")
        self.assertEqual(merged["INFISICAL_SECRETS_LOADED"], "1")
        self.assertEqual(created[0].token, "st.example")
        self.assertEqual(created[0].auth.universal_auth.logged, [])
        self.assertEqual(created[0].secrets.kwargs["project_id"], "proj-1")
        self.assertEqual(created[0].secrets.kwargs["secret_path"], "/baicao")
        self.assertTrue(created[0].closed)

    def test_universal_auth_then_list_secrets(self):
        created: list[FakeClient] = []

        def factory(**kwargs):
            client = FakeClient(**kwargs)
            client.secrets = _SecretsApi([_Secret("REDIS_URL", "redis://secret")])
            created.append(client)
            return client

        merged = self.mod.build_injected_env(
            {
                "INFISICAL_CLIENT_ID": "client",
                "INFISICAL_CLIENT_SECRET": "secret",
                "INFISICAL_API_URL": "https://app.infisical.com",
                "INFISICAL_PROJECT_ID": "proj-1",
            },
            client_factory=factory,
        )

        self.assertEqual(merged["REDIS_URL"], "redis://secret")
        self.assertIsNone(created[0].token)
        self.assertEqual(created[0].auth.universal_auth.logged, [("client", "secret")])

    def test_missing_project_id_fails(self):
        with self.assertRaises(self.mod.InfisicalEnvError) as raised:
            self.mod.build_injected_env(
                {
                    "INFISICAL_TOKEN": "st.example",
                    "INFISICAL_API_URL": "https://app.infisical.com",
                }
            )
        self.assertIn("INFISICAL_PROJECT_ID", str(raised.exception))

    def test_pass_through_without_auth(self):
        env = {"DATABASE_URL": "postgres://local", "INFISICAL_API_URL": "https://app.infisical.com"}
        self.assertEqual(self.mod.build_injected_env(env)["DATABASE_URL"], "postgres://local")
        self.assertNotIn("INFISICAL_SECRETS_LOADED", self.mod.build_injected_env(env))

    def test_tls_error_is_visible(self):
        def factory(**kwargs):
            del kwargs
            raise ssl.SSLCertVerificationError("certificate has expired")

        with self.assertRaises(self.mod.InfisicalEnvError) as raised:
            self.mod.build_injected_env(
                {
                    "INFISICAL_TOKEN": "st.example",
                    "INFISICAL_API_URL": "https://app.infisical.com",
                    "INFISICAL_PROJECT_ID": "proj-1",
                },
                client_factory=factory,
            )
        self.assertIn("TLS", str(raised.exception))

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
