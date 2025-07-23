import unittest
import os
import json
import subprocess
import shutil
from unittest.mock import patch
from click.testing import CliRunner
from cli.commands.link import link_account
from cli.commands.add import add_account

class TestLinkCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_test_repo"
        os.makedirs(self.test_dir, exist_ok=True)
        os.chdir(self.test_dir)
        # Set up a dummy config with one account
        # Manually create a dummy config file for testing
        dummy_config = {
            "accounts": [
                {
                    "name": "test_account",
                    "username": "test_user",
                    "gpg_key_id": "GPG_KEY_1",
                    "ssh_key_path": "~/.ssh/id_rsa_test"
                }
            ],
            "active": "test_account"
        }
        with open(self.config_path, "w") as f:
            json.dump(dummy_config, f, indent=2)

    def tearDown(self):
        os.chdir("..")
        # Use shutil to safely remove the directory and its contents
        import shutil
        shutil.rmtree(self.test_dir)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_link_fails_outside_git_repo(self):
        result = self.runner.invoke(link_account, ["test_account"], catch_exceptions=False)
        self.assertIn("This does not appear to be a git repository", result.output)
        self.assertFalse(os.path.exists(".ghmulti"))

    def test_link_succeeds_in_git_repo(self):
        subprocess.run(["git", "init"], capture_output=True)
        result = self.runner.invoke(link_account, ["test_account"], catch_exceptions=False)
        self.assertIn("Successfully linked account 'test_account'", result.output)
        self.assertTrue(os.path.exists(".ghmulti"))
        with open(".ghmulti", "r") as f:
            project_config = json.load(f)
        self.assertEqual(project_config["account"], "test_account")

        # Check local git config
        local_user = subprocess.check_output(["git", "config", "--local", "user.name"]).decode().strip()
        self.assertEqual(local_user, "test_user")
        local_email = subprocess.check_output(["git", "config", "--local", "user.email"]).decode().strip()
        self.assertEqual(local_email, "test_user@users.noreply.github.com")
        local_gpg = subprocess.check_output(["git", "config", "--local", "user.signingkey"]).decode().strip()
        self.assertEqual(local_gpg, "GPG_KEY_1")
        local_ssh = subprocess.check_output(["git", "config", "--local", "core.sshCommand"]).decode().strip()
        self.assertEqual(local_ssh, f"ssh -i {os.path.expanduser('~/.ssh/id_rsa_test')}")

    def test_link_fails_with_nonexistent_account(self):
        subprocess.run(["git", "init"], capture_output=True)
        result = self.runner.invoke(link_account, ["nonexistent_account"], catch_exceptions=False)
        self.assertIn("Account 'nonexistent_account' not found", result.output)
        self.assertFalse(os.path.exists(".ghmulti"))

if __name__ == '__main__':
    unittest.main()