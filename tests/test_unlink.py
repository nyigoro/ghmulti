import json
import os
import shutil
import subprocess
import unittest

from click.testing import CliRunner

from cli.commands.link import link_account
from cli.commands.unlink import unlink_account


class TestUnlinkCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_unlink_repo"
        os.makedirs(self.test_dir, exist_ok=True)
        os.chdir(self.test_dir)
        subprocess.run(["git", "init"], capture_output=True, check=False)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "accounts": [
                        {"name": "work", "username": "work_user"}
                    ],
                    "active": "work"
                },
                f,
                indent=2
            )

    def tearDown(self):
        os.chdir("..")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_unlink_after_link(self):
        link_result = self.runner.invoke(link_account, ["work"], catch_exceptions=False)
        self.assertEqual(link_result.exit_code, 0)
        self.assertTrue(os.path.exists(".ghmulti"))

        result = self.runner.invoke(unlink_account, catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Unlinked repository from account 'work'", result.output)
        self.assertFalse(os.path.exists(".ghmulti"))

    def test_unlink_json(self):
        self.runner.invoke(link_account, ["work"], catch_exceptions=False)
        result = self.runner.invoke(unlink_account, ["--json"], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertTrue(payload["unlinked"])
        self.assertEqual(payload["previously_linked_account"], "work")

    def test_unlink_non_git_repo_fails(self):
        non_git_dir = "temp_non_git_dir"
        os.makedirs(non_git_dir, exist_ok=True)
        os.chdir(non_git_dir)
        result = self.runner.invoke(unlink_account)
        os.chdir("..")
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("does not appear to be a git repository", result.output)


if __name__ == "__main__":
    unittest.main()
