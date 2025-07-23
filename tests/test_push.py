import unittest
import os
import json
import subprocess
import shutil
from unittest.mock import patch, MagicMock, call
from click.testing import CliRunner

# Import the commands from your CLI application
from cli.commands.push import push
from cli.commands.add import add_account
from cli.commands.use import use_account
from cli.commands.link import link_account

class TestPushCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_push_repo"
        os.makedirs(self.test_dir, exist_ok=True)
        os.chdir(self.test_dir)

        # Ensure clean state for config file
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        # Manually create a dummy config file for testing
        dummy_config = {
            "accounts": [
                {
                    "name": "global_acc",
                    "username": "global_user",
                },
                {
                    "name": "linked_acc",
                    "username": "linked_user",
                }
            ],
            "active": "global_acc"
        }
        with open(self.config_path, "w") as f:
            json.dump(dummy_config, f, indent=2)

        # Mock keyring.get_password for use_account/link_account calls
        self.keyring_patch = patch('keyring.get_password', return_value="dummy_token")
        self.mock_keyring_get_password = self.keyring_patch.start()

        # Initialize a git repo in the test directory
        # These are actual subprocess calls, not mocked by the test methods' patches
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/test/test.git"], capture_output=True)
        subprocess.run(["git", "remote", "add", "origin-linked_acc", "https://github.com/linked_user/test.git"], capture_output=True)

    def tearDown(self):
        os.chdir("..")
        shutil.rmtree(self.test_dir)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.keyring_patch.stop()

    @patch('subprocess.run')
    @patch('subprocess.check_output')
    def test_push_with_global_account(self, mock_subprocess_check_output, mock_subprocess_run):
        mock_subprocess_check_output.return_value = b"origin\norigin-linked_acc\n"
        result = self.runner.invoke(push, catch_exceptions=False)

        mock_subprocess_run.assert_any_call(
            ['git', 'push', 'origin', 'main'],
            check=True,
            env=unittest.mock.ANY
        )
        self.assertIn("Push successful", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run')
    @patch('subprocess.check_output')
    def test_push_with_linked_account(self, mock_subprocess_check_output, mock_subprocess_run):
        mock_subprocess_check_output.return_value = b"origin\norigin-linked_acc\n"
        self.runner.invoke(link_account, ["linked_acc"], catch_exceptions=False)
        result = self.runner.invoke(push, catch_exceptions=False)

        mock_subprocess_run.assert_any_call(
            ['git', 'push', 'origin-linked_acc', 'main'],
            check=True,
            env=unittest.mock.ANY
        )
        self.assertIn("Push successful", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run')
    @patch('subprocess.check_output')
    def test_push_with_explicit_remote(self, mock_subprocess_check_output, mock_subprocess_run):
        mock_subprocess_check_output.return_value = b"origin\norigin-linked_acc\n"
        self.runner.invoke(link_account, ["linked_acc"], catch_exceptions=False)
        result = self.runner.invoke(push, ["--remote", "origin"], catch_exceptions=False)

        mock_subprocess_run.assert_any_call(
            ['git', 'push', 'origin', 'main'],
            check=True,
            env=unittest.mock.ANY
        )
        self.assertIn("Push successful", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run')
    @patch('subprocess.check_output')
    def test_push_with_message(self, mock_subprocess_check_output, mock_subprocess_run):
        mock_subprocess_check_output.return_value = b"origin\n"
        result = self.runner.invoke(push, ["--message", "Test commit"], catch_exceptions=False)

        mock_subprocess_run.assert_any_call(['git', 'add', '.'], check=True)
        mock_subprocess_run.assert_any_call(['git', 'commit', '-m', 'Test commit'], check=True)
        mock_subprocess_run.assert_any_call(
            ['git', 'push', 'origin', 'main'],
            check=True,
            env=unittest.mock.ANY
        )
        self.assertIn("Push successful", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, "git push"))
    @patch('subprocess.check_output')
    def test_push_failure(self, mock_subprocess_check_output, mock_subprocess_run):
        mock_subprocess_check_output.return_value = b"origin\n"
        result = self.runner.invoke(push, catch_exceptions=False)

        self.assertIn("Git command failed", result.output)
        self.assertEqual(result.exit_code, 1)

if __name__ == '__main__':
    unittest.main()