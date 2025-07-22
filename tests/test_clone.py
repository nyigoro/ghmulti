import unittest
import os
import json
import subprocess
import shutil
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from cli.commands.clone import clone_repo
from cli.commands.add import add_account

class TestCloneCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_clone_test"
        os.makedirs(self.test_dir, exist_ok=True)
        os.chdir(self.test_dir)

        # Ensure clean state for config file
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        # Manually create a dummy config file for testing
        dummy_config = {
            "accounts": [
                {
                    "name": "test_account",
                    "username": "test_user",
                }
            ],
            "active": "test_account"
        }
        with open(self.config_path, "w") as f:
            json.dump(dummy_config, f, indent=2)

        # Mock keyring.get_password
        self.keyring_patch = patch('keyring.get_password', return_value="dummy_token")
        self.mock_keyring_get_password = self.keyring_patch.start()

    def tearDown(self):
        os.chdir("..")
        shutil.rmtree(self.test_dir)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.keyring_patch.stop()

    import unittest.mock
    import unittest.mock
    @patch('subprocess.run')
    @patch('os.chdir')
    def test_clone_without_linking(self, mock_chdir, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0) # Mock git clone success
        
        result = self.runner.invoke(clone_repo, ["https://github.com/test/repo.git"], catch_exceptions=False)
        
        mock_subprocess_run.assert_any_call(['git', 'clone', 'https://github.com/test/repo.git'], check=True, env=unittest.mock.ANY)
        # Verify env contents if a token is expected (in this case, no token, so just check it's a dict)
        call_args, call_kwargs = mock_subprocess_run.call_args
        self.assertIsInstance(call_kwargs["env"], dict)

        self.assertIn("Successfully cloned", result.output)
        self.assertIn("No account specified for linking", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run')
    @patch('os.chdir')
    def test_clone_with_linking(self, mock_chdir, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0) # Mock git clone and ghmulti link success

        result = self.runner.invoke(clone_repo, ["https://github.com/test/repo.git", "--account", "test_account"], catch_exceptions=False)
        
        mock_subprocess_run.assert_any_call(['git', 'clone', 'https://github.com/test/repo.git'], check=True, env=unittest.mock.ANY)
        # Verify env contents for cloning with token
        call_args, call_kwargs = mock_subprocess_run.call_args_list[0] # First call is git clone
        self.assertIn("GIT_ASKPASS", call_kwargs["env"])
        self.assertIn("GIT_USERNAME", call_kwargs["env"])
        self.assertIn("GIT_PASSWORD", call_kwargs["env"])
        self.assertEqual(call_kwargs["env"]["GIT_USERNAME"], "test_user")
        self.assertEqual(call_kwargs["env"]["GIT_PASSWORD"], "dummy_token")

        mock_subprocess_run.assert_any_call(['ghmulti', 'link', 'test_account'], check=True)
        self.assertIn("Successfully cloned", result.output)
        self.assertIn("Linking repository to account 'test_account'", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, "git clone"))
    @patch('os.chdir')
    def test_clone_failure(self, mock_chdir, mock_subprocess_run):
        result = self.runner.invoke(clone_repo, ["https://github.com/test/repo.git"], catch_exceptions=False)
        self.assertIn("Git clone failed", result.output)
        self.assertEqual(result.exit_code, 1)

    @patch('subprocess.run')
    @patch('os.chdir')
    @patch('click.confirm', return_value=True) # Simulate user confirming to link
    @patch('cli.config.get_active_account', return_value={'name': 'test_account', 'username': 'test_user'})
    def test_clone_interactive_linking(self, mock_get_active_account, mock_click_confirm, mock_chdir, mock_subprocess_run):
        # Configure mock_subprocess_run to handle different calls
        def subprocess_run_side_effect(cmd, **kwargs):
            if cmd[0] == 'git' and cmd[1] == 'clone':
                return MagicMock(returncode=0) # Mock git clone success
            elif cmd[0] == 'ghmulti':
                return MagicMock(returncode=0) # Mock ghmulti use/link success
            raise Exception(f"Unexpected subprocess call: {cmd}")

        mock_subprocess_run.side_effect = subprocess_run_side_effect

        result = self.runner.invoke(clone_repo, ["https://github.com/test/repo.git"], catch_exceptions=False)
        
        mock_subprocess_run.assert_any_call(['git', 'clone', 'https://github.com/test/repo.git'], check=True, env=unittest.mock.ANY)
        mock_subprocess_run.assert_any_call(['ghmulti', 'use'], check=True) # Check for interactive use
        mock_subprocess_run.assert_any_call(['ghmulti', 'link', 'test_account'], check=True)
        self.assertIn("Successfully cloned", result.output)
        self.assertIn("Linking repository to globally active account 'test_account'", result.output)
        self.assertEqual(result.exit_code, 0)

if __name__ == '__main__':
    unittest.main()
