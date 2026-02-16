import json
import os
import shutil
import subprocess
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from cli.commands.status import status


class TestStatusCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_status_repo"
        os.makedirs(self.test_dir, exist_ok=True)
        os.chdir(self.test_dir)

        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "accounts": [
                        {"name": "global_account", "username": "global_user"},
                        {"name": "linked_account", "username": "linked_user"},
                    ],
                    "active": "global_account"
                },
                f,
                indent=2
            )

        subprocess.run(["git", "init"], capture_output=True, check=False)
        subprocess.run(["git", "config", "--local", "user.name", "global_user"], capture_output=True, check=False)
        subprocess.run(["git", "config", "--local", "user.email", "global_user@users.noreply.github.com"], capture_output=True, check=False)

        self.keyring_patch = patch("keyring.get_password", return_value="dummy_token")
        self.keyring_patch.start()

    def tearDown(self):
        os.chdir("..")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.keyring_patch.stop()

    def test_status_json_has_expected_shape(self):
        result = self.runner.invoke(status, ["--json", "--skip-token-check"], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertIn("linked_account", payload)
        self.assertIn("global_active_account", payload)
        self.assertIn("effective_active_account", payload)
        self.assertIn("local_git", payload)
        self.assertIn("global_git", payload)
        self.assertIn("token", payload)
        self.assertIn("warnings", payload)

    def test_status_when_no_active_account(self):
        with open(self.config_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["active"] = None
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        result = self.runner.invoke(status, ["--json", "--skip-token-check"], catch_exceptions=False)
        payload = json.loads(result.output)
        self.assertIsNone(payload["global_active_account"])
        self.assertIsNone(payload["effective_active_account"])

    def test_status_uses_linked_account_from_project_file(self):
        with open(".ghmulti", "w", encoding="utf-8") as f:
            json.dump({"account": "linked_account"}, f, indent=2)

        result = self.runner.invoke(status, ["--json", "--skip-token-check"], catch_exceptions=False)
        payload = json.loads(result.output)
        self.assertEqual(payload["linked_account"], "linked_account")
        self.assertEqual(payload["effective_active_account"]["name"], "linked_account")

    def test_status_reports_git_user_mismatch_warning(self):
        subprocess.run(["git", "config", "--local", "user.name", "different_name"], capture_output=True, check=False)
        result = self.runner.invoke(status, ["--json", "--skip-token-check"], catch_exceptions=False)
        payload = json.loads(result.output)
        self.assertTrue(any("does not match" in warning for warning in payload["warnings"]))

    def test_status_text_output(self):
        result = self.runner.invoke(status, ["--skip-token-check"], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Checking ghmulti status", result.output)
        self.assertIn("Global active account", result.output)
        self.assertIn("Effective active account", result.output)


if __name__ == "__main__":
    unittest.main()
