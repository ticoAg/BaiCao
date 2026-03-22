import importlib.util
import unittest
from pathlib import Path


def load_runtime_module():
    runtime_path = Path(__file__).resolve().parents[1] / "dev_runtime.py"
    spec = importlib.util.spec_from_file_location("dev_runtime", runtime_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RuntimeHelpTests(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime_module()

    def test_root_help_lists_supported_resources(self):
        exit_code, output = self.runtime.run_cli(["help"], env={})

        self.assertEqual(exit_code, 0)
        self.assertIn("deps", output)
        self.assertIn("api", output)
        self.assertIn("stack", output)

    def test_unknown_resource_suggests_help(self):
        exit_code, output = self.runtime.run_cli(["ap", "up"], env={})

        self.assertEqual(exit_code, 2)
        self.assertIn("Unknown resource: ap", output)
        self.assertIn("Did you mean: api", output)
        self.assertIn("make help", output)

    def test_unknown_action_suggests_resource_help(self):
        exit_code, output = self.runtime.run_cli(["api", "upp"], env={})

        self.assertEqual(exit_code, 2)
        self.assertIn("Unknown action: upp", output)
        self.assertIn("make api help", output)
