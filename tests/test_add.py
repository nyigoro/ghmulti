import unittest
import os
import json
from click.testing import CliRunner
from cli.commands.add import add_account

class TestAddCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_add_account(self):
        result = self.runner.invoke(add_account, input='test_account\ntest_user\ntest_token')
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Added account 'test_account' and saved.", result.output)

        with open(self.config_path, "r") as f:
            config = json.load(f)
        
        self.assertEqual(len(config["accounts"]), 1)
        self.assertEqual(config["accounts"][0]["name"], "test_account")
        self.assertEqual(config["accounts"][0]["username"], "test_user")

if __name__ == '__main__':
    unittest.main()
