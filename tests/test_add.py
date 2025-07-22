import unittest
import os
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from cli.commands.add import add_account

class TestAddCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        # Mock keyring.set_password to prevent actual keyring interaction
        self.keyring_patch = patch('keyring.set_password')
        self.mock_keyring = self.keyring_patch.start()

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        self.keyring_patch.stop()

    @patch('builtins.input', side_effect=['test_account_token', 'test_user_token', 'test_token_value', '', ''])
    def test_add_account_with_token(self, mock_input):
        result = self.runner.invoke(add_account)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Added account 'test_account_token' and saved.", result.output)
        self.mock_keyring.assert_called_once_with("ghmulti", "test_user_token", "test_token_value")

    @patch('builtins.input', side_effect=['test_account_ssh', 'test_user_ssh', '', '', '~/.ssh/id_rsa_test'])
    def test_add_account_with_ssh_key(self, mock_input):
        # Reset mock calls for this test
        self.mock_keyring.reset_mock()
        result = self.runner.invoke(add_account)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Added account 'test_account_ssh' and saved.", result.output)
        # Verify keyring.set_password was NOT called for this case
        self.mock_keyring.assert_not_called()

    @patch('builtins.input', side_effect=['test_account_fail', 'test_user_fail', '', '', ''])
    def test_add_account_missing_credentials(self, mock_input):
        # Reset mock calls for this test
        self.mock_keyring.reset_mock()
        result = self.runner.invoke(add_account)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("❌ Either a Personal Access Token or an SSH Key Path is required.", result.output)

if __name__ == '__main__':
    unittest.main()
