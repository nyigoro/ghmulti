import json
import os
import shutil
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from cli.commands.remove import remove_account
from cli.commands.rename import rename_account
from cli.commands.update import update_account


class TestAccountLifecycle(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.test_dir = "temp_account_lifecycle"
        os.makedirs(self.test_dir, exist_ok=True)
        os.chdir(self.test_dir)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "accounts": [
                        {"name": "work", "username": "work_user"},
                        {"name": "personal", "username": "personal_user"},
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

    def test_rename_updates_active_and_project_link(self):
        with open(".ghmulti", "w", encoding="utf-8") as f:
            json.dump({"account": "work"}, f, indent=2)

        result = self.runner.invoke(rename_account, ["work", "company"], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["active"], "company")
        self.assertTrue(any(account["name"] == "company" for account in data["accounts"]))

        with open(".ghmulti", "r", encoding="utf-8") as f:
            project = json.load(f)
        self.assertEqual(project["account"], "company")

    @patch("keyring.get_password", return_value="old_token")
    @patch("keyring.set_password")
    @patch("keyring.delete_password")
    def test_update_changes_username_and_token(self, mock_delete, mock_set, mock_get):
        result = self.runner.invoke(
            update_account,
            ["work", "--username", "work_user_new", "--token", "new_token", "--set-active"],
            catch_exceptions=False
        )
        self.assertEqual(result.exit_code, 0)
        mock_delete.assert_called_once_with("ghmulti", "work_user")
        mock_set.assert_called_once_with("ghmulti", "work_user_new", "new_token")

    @patch("keyring.delete_password")
    def test_remove_account(self, mock_delete):
        result = self.runner.invoke(remove_account, ["personal", "--yes"], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertFalse(any(account["name"] == "personal" for account in data["accounts"]))
        mock_delete.assert_called_once_with("ghmulti", "personal_user")


if __name__ == "__main__":
    unittest.main()
