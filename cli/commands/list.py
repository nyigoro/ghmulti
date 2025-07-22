# ghmulti/command/list.py

import os
import json
import sys

CONFIG_PATH = os.path.expanduser("~/.ghmulti.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("❌ No config file found. Run `add` first.")
        sys.exit(1)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def list_accounts():
    config = load_config()
    accounts = config.get("accounts", [])
    active = config.get("active")

    if not accounts:
        print("⚠️  No accounts configured.")
        return

    print("📘 Configured GitHub accounts:\n")

    for acc in accounts:
        name = acc.get("name", "<unnamed>")
        user = acc.get("user", "")
        email = acc.get("email", "")
        mark = "✅" if name == active else "  "
        print(f"{mark} {name}\n    └─ {user} <{email}>")
