import json
import os
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from cli.commands.add import add_account


class TestAddCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.keyring_patch = patch("keyring.set_password")
        self.mock_keyring = self.keyring_patch.start()

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.keyring_patch.stop()

    def test_add_account_with_token(self):
        user_input = "\n".join([
            "test_account_token",
            "test_user_token",
            "test_token_value",
            "",
            "",
            ""
        ]) + "\n"
        result = self.runner.invoke(add_account, input=user_input)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Added account 'test_account_token' and saved.", result.output)
        self.mock_keyring.assert_called_once_with("ghmulti", "test_user_token", "test_token_value")

    def test_add_account_with_ssh_key(self):
        user_input = "\n".join([
            "test_account_ssh",
            "test_user_ssh",
            "",
            "",
            "~/.ssh/id_rsa_test"
        ]) + "\n"
        result = self.runner.invoke(add_account, input=user_input)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Added account 'test_account_ssh' and saved.", result.output)
        self.mock_keyring.assert_not_called()

    def test_add_account_missing_credentials(self):
        user_input = "\n".join([
            "test_account_fail",
            "test_user_fail",
            "",
            "",
            ""
        ]) + "\n"
        result = self.runner.invoke(add_account, input=user_input)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Either a Personal Access Token or an SSH Key Path is required.", result.output)

    def test_add_account_with_flags(self):
        result = self.runner.invoke(
            add_account,
            [
                "--name", "work",
                "--username", "work-user",
                "--token", "tok_123",
                "--set-active"
            ]
        )
        self.assertEqual(result.exit_code, 0)
        with open(self.config_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["active"], "work")
        self.assertEqual(payload["accounts"][0]["name"], "work")


if __name__ == "__main__":
    unittest.main()
