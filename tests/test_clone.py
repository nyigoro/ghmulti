import json
import os
import shutil
import subprocess
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from click.testing import CliRunner

from cli.commands.clone import clone_repo


class TestCloneCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_clone_test"
        os.makedirs(self.test_dir, exist_ok=True)
        os.chdir(self.test_dir)

        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "accounts": [{"name": "test_account", "username": "test_user"}],
                    "active": "test_account"
                },
                f,
                indent=2
            )

        self.keyring_patch = patch("keyring.get_password", return_value="dummy_token")
        self.keyring_patch.start()

    def tearDown(self):
        os.chdir("..")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.keyring_patch.stop()

    @patch("subprocess.run")
    def test_clone_without_linking(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        result = self.runner.invoke(
            clone_repo,
            ["https://github.com/test/repo.git", "--no-link"],
            catch_exceptions=False
        )

        mock_subprocess_run.assert_any_call(
            ["git", "clone", "https://github.com/test/repo.git"],
            check=True,
            env=unittest.mock.ANY
        )
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Successfully cloned", result.output)
        self.assertIn("No account specified for linking", result.output)

    @patch("cli.commands.clone.link_account_logic")
    @patch("subprocess.run")
    def test_clone_with_linking(self, mock_subprocess_run, mock_link_logic):
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        result = self.runner.invoke(
            clone_repo,
            ["https://github.com/test/repo.git", "--account", "test_account", "--link"],
            catch_exceptions=False
        )

        mock_subprocess_run.assert_any_call(
            ["git", "clone", "https://github.com/test/repo.git"],
            check=True,
            env=unittest.mock.ANY
        )
        mock_link_logic.assert_called_once_with("test_account", repo_path="repo")
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Linking repository to account 'test_account'", result.output)

    @patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git clone"))
    def test_clone_failure(self, mock_subprocess_run):
        result = self.runner.invoke(
            clone_repo,
            ["https://github.com/test/repo.git", "--no-link"],
            catch_exceptions=False
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Git clone failed", result.output)

    @patch("inquirer.prompt", return_value={"account": "test_account"})
    @patch("click.confirm", return_value=True)
    @patch("cli.commands.clone.link_account_logic")
    @patch("subprocess.run")
    def test_clone_interactive_linking(self, mock_subprocess_run, mock_link_logic, mock_confirm, mock_prompt):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        result = self.runner.invoke(
            clone_repo,
            ["https://github.com/test/repo.git"],
            catch_exceptions=False
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_link_logic.assert_called_once_with("test_account", repo_path="repo")


if __name__ == "__main__":
    unittest.main()
