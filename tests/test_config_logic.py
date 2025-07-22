import unittest
import os
import json
from unittest.mock import patch, mock_open
from pathlib import Path

# Import the functions to be tested
from cli.config import load_config, save_config, get_active_account, get_linked_account, get_token, CONFIG_PATH, PROJECT_CONFIG_FILE

class TestConfigLogic(unittest.TestCase):

    def setUp(self):
        # Mock CONFIG_PATH and PROJECT_CONFIG_FILE to point to temporary paths
        self.mock_config_path = Path("/tmp/test_ghmulti.json")
        self.mock_project_config_file = Path("/tmp/.ghmulti_project")

        # Ensure parent directories exist for mock files
        self.mock_config_path.parent.mkdir(parents=True, exist_ok=True)
        self.mock_project_config_file.parent.mkdir(parents=True, exist_ok=True)

        # Patch the constants in the module under test
        self.patcher_config_path = patch('cli.config.CONFIG_PATH', self.mock_config_path)
        self.patcher_project_config_file = patch('cli.config.PROJECT_CONFIG_FILE', self.mock_project_config_file)
        self.patcher_config_path.start()
        self.patcher_project_config_file.start()

        # Ensure clean state for mock files
        if self.mock_config_path.exists():
            os.remove(self.mock_config_path)
        if self.mock_project_config_file.exists():
            os.remove(self.mock_project_config_file)

    def tearDown(self):
        # Clean up mock files
        if self.mock_config_path.exists():
            os.remove(self.mock_config_path)
        if self.mock_project_config_file.exists():
            os.remove(self.mock_project_config_file)

        # Stop patching
        self.patcher_config_path.stop()
        self.patcher_project_config_file.stop()

    def _create_dummy_config(self, data):
        with open(self.mock_config_path, "w") as f:
            json.dump(data, f)

    def _create_dummy_project_config(self, account_name):
        with open(self.mock_project_config_file, "w") as f:
            json.dump({"account": account_name}, f)

    def test_load_config_no_file(self):
        config = load_config()
        self.assertEqual(config, {"accounts": [], "active": None})

    def test_load_config_existing_file(self):
        dummy_data = {"accounts": [{"name": "test", "username": "user"}], "active": "test"}
        self._create_dummy_config(dummy_data)
        config = load_config()
        self.assertEqual(config, dummy_data)

    def test_save_config(self):
        dummy_data = {"accounts": [{"name": "new", "username": "new_user"}], "active": "new"}
        save_config(dummy_data)
        with open(self.mock_config_path, "r") as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, dummy_data)

    def test_get_linked_account_no_file(self):
        linked_account = get_linked_account()
        self.assertIsNone(linked_account)

    def test_get_linked_account_existing_file(self):
        self._create_dummy_project_config("project_acc")
        linked_account = get_linked_account()
        self.assertEqual(linked_account, "project_acc")

    def test_get_linked_account_malformed_json(self):
        with open(self.mock_project_config_file, "w") as f:
            f.write("invalid json")
        linked_account = get_linked_account()
        self.assertIsNone(linked_account)

    @patch('cli.config.get_linked_account', return_value=None)
    def test_get_active_account_no_accounts(self, mock_get_linked_account):
        self._create_dummy_config({"accounts": [], "active": None})
        active_acc = get_active_account()
        self.assertIsNone(active_acc)

    @patch('cli.config.get_linked_account', return_value=None)
    def test_get_active_account_global_only(self, mock_get_linked_account):
        dummy_data = {"accounts": [{"name": "global_acc", "username": "global_user"}], "active": "global_acc"}
        self._create_dummy_config(dummy_data)
        active_acc = get_active_account()
        self.assertEqual(active_acc, {"name": "global_acc", "username": "global_user"})

    @patch('cli.config.get_linked_account', return_value="linked_acc")
    def test_get_active_account_linked_prioritized(self, mock_get_linked_account):
        dummy_data = {
            "accounts": [
                {"name": "global_acc", "username": "global_user"},
                {"name": "linked_acc", "username": "linked_user"}
            ],
            "active": "global_acc" # Global is 'global_acc', but linked is 'linked_acc'
        }
        self._create_dummy_config(dummy_data)
        active_acc = get_active_account()
        self.assertEqual(active_acc, {"name": "linked_acc", "username": "linked_user"})

    @patch('cli.config.get_linked_account', return_value="nonexistent_linked_acc")
    def test_get_active_account_linked_nonexistent_falls_back_to_global(self, mock_get_linked_account):
        dummy_data = {
            "accounts": [
                {"name": "global_acc", "username": "global_user"}
            ],
            "active": "global_acc"
        }
        self._create_dummy_config(dummy_data)
        active_acc = get_active_account()
        self.assertEqual(active_acc, {"name": "global_acc", "username": "global_user"})

    @patch('keyring.get_password', return_value="mock_token_123")
    def test_get_token(self, mock_keyring_get_password):
        token = get_token("test_user")
        self.assertEqual(token, "mock_token_123")
        mock_keyring_get_password.assert_called_once_with("ghmulti", "test_user")

if __name__ == '__main__':
    unittest.main()
