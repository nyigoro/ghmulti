import unittest
import os
import json
import subprocess
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from cli.commands.status import status
from cli.commands.add import add_account
from cli.commands.link import link_account
from cli.commands.use import use_account

class TestStatusCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_status_repo"
        os.makedirs(self.test_dir, exist_ok=True)
        os.chdir(self.test_dir)

        # Ensure clean state for config file
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        # Manually create a dummy config file for testing
        dummy_config = {
            "accounts": [
                {
                    "name": "global_account",
                    "username": "global_user",
                },
                {
                    "name": "linked_account",
                    "username": "linked_user",
                }
            ],
            "active": "global_account"
        }
        with open(self.config_path, "w") as f:
            json.dump(dummy_config, f, indent=2)

        # Mock keyring.set_password as it would be called by add_account
        self.keyring_patch = patch('keyring.set_password')
        self.mock_keyring = self.keyring_patch.start()

        # Initialize a git repo
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(["git", "config", "user.name", "test_git_user"], capture_output=True)
        subprocess.run(["git", "config", "user.email", "test_git_user@example.com"], capture_output=True)

    def tearDown(self):
        os.chdir("..")
        import shutil
        shutil.rmtree(self.test_dir)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        # Clean up keyring entries if any were set by tests (though mocks should prevent this)
        with patch('keyring.delete_password') as mock_delete:
            mock_delete("ghmulti", "global_user")
            mock_delete("ghmulti", "linked_user")

    @patch('keyring.get_password', return_value="dummy_token")
    @patch('subprocess.run')
    def test_status_no_active_account(self, mock_subprocess_run, mock_keyring_get_password):
        # Remove active account from config for this test
        with open(self.config_path, "r+") as f:
            config = json.load(f)
            config["active"] = None
            f.seek(0)
            json.dump(config, f, indent=2)
            f.truncate()

        result = self.runner.invoke(status, catch_exceptions=False)
        self.assertIn("No active account configured", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('keyring.get_password', return_value="dummy_token")
    @patch('subprocess.check_output', side_effect=lambda cmd, **kwargs: b"test_git_user" if "user.name" in cmd else (b"test_git_user@example.com" if "user.email" in cmd else b""))
    @patch('subprocess.run')
    def test_status_global_active_account(self, mock_subprocess_run, mock_subprocess_check_output, mock_keyring_get_password):
        self.runner.invoke(use_account, ["global_account"], catch_exceptions=False)
        mock_subprocess_run.return_value = MagicMock(returncode=0) # Mock curl success

        result = self.runner.invoke(status, catch_exceptions=False)
        self.assertIn("Active account: 'global_account' (global_user)", result.output)
        self.assertIn("Git config user: test_git_user <test_git_user@example.com>", result.output)
        self.assertIn("Token is valid and has access to user data.", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('keyring.get_password', return_value="dummy_token")
    @patch('subprocess.check_output', side_effect=lambda cmd, **kwargs: b"linked_user" if "user.name" in cmd else (b"linked_user@example.com" if "user.email" in cmd else b""))
    @patch('subprocess.run')
    def test_status_linked_account(self, mock_subprocess_run, mock_subprocess_check_output, mock_keyring_get_password):
        self.runner.invoke(link_account, ["linked_account"], catch_exceptions=False)
        mock_subprocess_run.return_value = MagicMock(returncode=0) # Mock curl success

        result = self.runner.invoke(status, catch_exceptions=False)
        self.assertIn("Repository linked to: 'linked_account' (via .ghmulti)", result.output)
        self.assertIn("Active account: 'linked_account' (linked_user)", result.output)
        self.assertIn("Git config user: linked_user <linked_user@example.com>", result.output)
        self.assertIn("Token is valid and has access to user data.", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('keyring.get_password', return_value="dummy_token")
    @patch('subprocess.check_output', side_effect=lambda cmd, **kwargs: b"mismatched_user" if "user.name" in cmd else (b"mismatched_user@example.com" if "user.email" in cmd else b""))
    @patch('subprocess.run')
    def test_status_git_user_mismatch(self, mock_subprocess_run, mock_subprocess_check_output, mock_keyring_get_password):
        self.runner.invoke(use_account, ["global_account"], catch_exceptions=False)
        mock_subprocess_run.return_value = MagicMock(returncode=0) # Mock curl success

        result = self.runner.invoke(status, catch_exceptions=False)
        self.assertIn("Active account: 'global_account' (global_user)", result.output)
        self.assertIn("Git config user: mismatched_user <mismatched_user@example.com>", result.output)
        self.assertIn("Warning: Git user.name does not match the active account username.", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('keyring.get_password', return_value="dummy_token")
    @patch('subprocess.check_output', side_effect=subprocess.CalledProcessError(1, "git config"))
    @patch('subprocess.run')
    def test_status_git_config_error(self, mock_subprocess_run, mock_subprocess_check_output, mock_keyring_get_password):
        self.runner.invoke(use_account, ["global_account"], catch_exceptions=False)
        mock_subprocess_run.return_value = MagicMock(returncode=0) # Mock curl success

        result = self.runner.invoke(status, catch_exceptions=False)
        self.assertIn("Warning: Could not read git user config.", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('keyring.get_password', return_value=None) # Simulate no token found
    @patch('subprocess.check_output', side_effect=lambda cmd, **kwargs: b"test_git_user" if "user.name" in cmd else (b"test_git_user@example.com" if "user.email" in cmd else b""))
    @patch('subprocess.run')
    def test_status_no_token_in_keyring(self, mock_subprocess_run, mock_subprocess_check_output, mock_keyring_get_password):
        self.runner.invoke(use_account, ["global_account"], catch_exceptions=False)

        result = self.runner.invoke(status, catch_exceptions=False)
        self.assertIn("Token not found for the active account in keychain.", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('keyring.get_password', return_value="dummy_token")
    @patch('subprocess.check_output', side_effect=lambda cmd, **kwargs: b"test_git_user" if "user.name" in cmd else (b"test_git_user@example.com" if "user.email" in cmd else b""))
    @patch('subprocess.run')
    def test_status_invalid_token(self, mock_subprocess_run, mock_subprocess_check_output, mock_keyring_get_password):
        # Configure mock_subprocess_run to raise CalledProcessError only for 'curl'
        def mock_run_side_effect(cmd, **kwargs):
            if isinstance(cmd, list) and "curl" in cmd[0]:
                raise subprocess.CalledProcessError(1, cmd='curl', output=b'', stderr=b'')
            return MagicMock(returncode=0) # For git commands

        mock_subprocess_run.side_effect = mock_run_side_effect

        self.runner.invoke(use_account, ["global_account"], catch_exceptions=False)

        result = self.runner.invoke(status, catch_exceptions=False)
        self.assertIn("Token is invalid or expired. Please update it using `ghmulti add`.", result.output)
        self.assertEqual(result.exit_code, 0)

if __name__ == '__main__':
    unittest.main()
