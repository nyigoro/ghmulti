import json
import os
import unittest

from click.testing import CliRunner

from cli.commands.doctor import doctor


class TestDoctorCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.config_path = os.path.expanduser("~/.ghmulti.json")
        self.original_config = None
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.original_config = f.read()

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "accounts": [{"name": "work", "username": "work_user"}],
                    "active": "work"
                },
                f,
                indent=2
            )

    def tearDown(self):
        if self.original_config is None:
            if os.path.exists(self.config_path):
                os.remove(self.config_path)
        else:
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(self.original_config)

    def test_doctor_json_output(self):
        result = self.runner.invoke(doctor, ["--json"], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.output)
        self.assertIn("ok", payload)
        self.assertIn("checks", payload)
        self.assertTrue(any(check["name"] == "git" for check in payload["checks"]))


if __name__ == "__main__":
    unittest.main()
