import unittest
import os
import json
import subprocess
import shutil
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from cli.commands.use import use_account
from cli.commands.add import add_account

class TestUseCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_use_test"
        os.makedirs(self.test_dir, exist_ok=True)
        os.chdir(self.test_dir)

        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        # Add some dummy accounts for testing
        dummy_config = {
            "accounts": [
                {
                    "name": "test_account_1",
                    "username": "user1",
                    "gpg_key_id": "GPG1",
                    "ssh_key_path": "~/.ssh/id_rsa_user1"
                },
                {
                    "name": "test_account_2",
                    "username": "user2",
                }
            ],
            "active": None
        }
        with open(self.config_path, "w") as f:
            json.dump(dummy_config, f, indent=2)

    def tearDown(self):
        os.chdir("..")
        shutil.rmtree(self.test_dir)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    @patch('subprocess.run')
    def test_use_account_sets_global_git_config(self, mock_subprocess_run):
        result = self.runner.invoke(use_account, ["test_account_1"], catch_exceptions=False)

        mock_subprocess_run.assert_any_call(["git", "config", "--global", "user.name", "user1"], check=True)
        mock_subprocess_run.assert_any_call(["git", "config", "--global", "user.email", "user1@users.noreply.github.com"], check=True)
        mock_subprocess_run.assert_any_call(["git", "config", "--global", "user.signingkey", "GPG1"], check=True)
        mock_subprocess_run.assert_any_call(["git", "config", "--global", "core.sshCommand", f"ssh -i {os.path.expanduser('~/.ssh/id_rsa_user1')}"], check=True)

        self.assertIn("Switched global active account to: test_account_1", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run')
    def test_use_account_unsets_optional_configs(self, mock_subprocess_run):
        # First, set test_account_1 as active to ensure optional configs are set
        self.runner.invoke(use_account, ["test_account_1"], catch_exceptions=False)

        # Then switch to test_account_2 which has no GPG or SSH key
        result = self.runner.invoke(use_account, ["test_account_2"], catch_exceptions=False)

        mock_subprocess_run.assert_any_call(["git", "config", "--global", "user.name", "user2"], check=True)
        mock_subprocess_run.assert_any_call(["git", "config", "--global", "user.email", "user2@users.noreply.github.com"], check=True)
        mock_subprocess_run.assert_any_call(["git", "config", "--global", "--unset-all", "user.signingkey"], check=False)
        mock_subprocess_run.assert_any_call(["git", "config", "--global", "--unset-all", "core.sshCommand"], check=False)

        self.assertIn("Switched global active account to: test_account_2", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('inquirer.prompt', return_value={'account': 'test_account_1'})
    @patch('subprocess.run')
    def test_use_account_interactive_mode(self, mock_subprocess_run, mock_inquirer_prompt):
        result = self.runner.invoke(use_account, [], catch_exceptions=False)

        mock_subprocess_run.assert_any_call(["git", "config", "--global", "user.name", "user1"], check=True)
        self.assertIn("Switched global active account to: test_account_1", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_use_account_nonexistent(self):
        result = self.runner.invoke(use_account, ["nonexistent_account"], catch_exceptions=False)
        self.assertIn("No account named 'nonexistent_account' found.", result.output)
        self.assertEqual(result.exit_code, 1)

if __name__ == '__main__':
    unittest.main()
