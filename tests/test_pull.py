import unittest
import os
import json
import subprocess
import shutil
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from cli.commands.pull import pull_repo
from cli.commands.add import add_account
from cli.commands.use import use_account
from cli.commands.link import link_account

class TestPullCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_pull_repo"
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

        # Mock keyring.get_password
        self.keyring_patch = patch('keyring.get_password', return_value="dummy_token")
        self.mock_keyring_get_password = self.keyring_patch.start()

        # Initialize a git repo
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/test/test.git"], capture_output=True)
        subprocess.run(["git", "remote", "add", "origin-linked_acc", "https://github.com/linked_user/test.git"], capture_output=True)

    def tearDown(self):
        os.chdir(".." )
        shutil.rmtree(self.test_dir)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.keyring_patch.stop()

    @patch('subprocess.run')
    @patch('subprocess.check_output')
    def test_pull_with_global_account(self, mock_subprocess_check_output, mock_subprocess_run):
        # Mock git remote output
        mock_subprocess_check_output.side_effect = [
            b"origin\norigin-linked_acc\n", # git remote
        ]

        # Ensure global_acc is active
        self.runner.invoke(use_account, ["global_acc"], catch_exceptions=False)
        
        result = self.runner.invoke(pull_repo, catch_exceptions=False)
        mock_subprocess_run.assert_called_once_with(
            ['git', 'pull', 'origin', 'main'],
            check=True,
            env=unittest.mock.ANY
        )
        # Verify the contents of the env dictionary
        call_args, call_kwargs = mock_subprocess_run.call_args
        self.assertIn("GIT_ASKPASS", call_kwargs["env"])
        self.assertIn("GIT_USERNAME", call_kwargs["env"])
        self.assertIn("GIT_PASSWORD", call_kwargs["env"])
        self.assertEqual(call_kwargs["env"]["GIT_USERNAME"], "global_user")
        self.assertEqual(call_kwargs["env"]["GIT_PASSWORD"], "dummy_token")

        self.assertIn("Pull successful", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run')
    @patch('subprocess.check_output')
    def test_pull_with_linked_account(self, mock_subprocess_check_output, mock_subprocess_run):
        # Mock git remote output
        mock_subprocess_check_output.side_effect = [
            b"origin\norigin-linked_acc\n", # git remote
        ]

        # Link to linked_acc
        self.runner.invoke(link_account, ["linked_acc"], catch_exceptions=False)

        result = self.runner.invoke(pull_repo, catch_exceptions=False)
        mock_subprocess_run.assert_called_once_with(
            ['git', 'pull', 'origin-linked_acc', 'main'],
            check=True,
            env=unittest.mock.ANY
        )
        # Verify the contents of the env dictionary
        call_args, call_kwargs = mock_subprocess_run.call_args
        self.assertIn("GIT_ASKPASS", call_kwargs["env"])
        self.assertIn("GIT_USERNAME", call_kwargs["env"])
        self.assertIn("GIT_PASSWORD", call_kwargs["env"])
        self.assertEqual(call_kwargs["env"]["GIT_USERNAME"], "linked_user")
        self.assertEqual(call_kwargs["env"]["GIT_PASSWORD"], "dummy_token")

        self.assertIn("Pull successful", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run')
    @patch('subprocess.check_output')
    def test_pull_with_explicit_remote(self, mock_subprocess_check_output, mock_subprocess_run):
        # Mock git remote output
        mock_subprocess_check_output.side_effect = [
            b"origin\norigin-linked_acc\n", # git remote
        ]

        # Link to linked_acc, but explicitly pull from origin
        self.runner.invoke(link_account, ["linked_acc"], catch_exceptions=False)

        result = self.runner.invoke(pull_repo, ["--remote", "origin"], catch_exceptions=False)
        mock_subprocess_run.assert_called_once_with(
            ['git', 'pull', 'origin', 'main'],
            check=True,
            env=unittest.mock.ANY
        )
        # Verify the contents of the env dictionary
        call_args, call_kwargs = mock_subprocess_run.call_args
        self.assertIn("GIT_ASKPASS", call_kwargs["env"])
        self.assertIn("GIT_USERNAME", call_kwargs["env"])
        self.assertIn("GIT_PASSWORD", call_kwargs["env"])
        self.assertEqual(call_kwargs["env"]["GIT_USERNAME"], "linked_user") # Should be linked_user as it's the active account
        self.assertEqual(call_kwargs["env"]["GIT_PASSWORD"], "dummy_token")

        self.assertIn("Pull successful", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, "git pull"))
    @patch('subprocess.check_output')
    def test_pull_failure(self, mock_subprocess_check_output, mock_subprocess_run):
        # Mock git remote output
        mock_subprocess_check_output.side_effect = [
            b"origin\n", # git remote
        ]
        result = self.runner.invoke(pull_repo, catch_exceptions=False)
        self.assertIn("Git pull failed", result.output)
        self.assertEqual(result.exit_code, 1)

if __name__ == '__main__':
    unittest.main()