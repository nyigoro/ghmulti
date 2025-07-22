# ghmulti/command/use.py

import os
import json
import sys

CONFIG_PATH = os.path.expanduser("~/.ghmulti.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("❌ Config file not found. Run `add` to create one.")
        sys.exit(1)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def use_account(account_name):
    config = load_config()

    accounts = config.get("accounts", [])
    match = next((a for a in accounts if a["name"] == account_name), None)

    if not match:
        print(f"❌ No account named '{account_name}' found.")
        sys.exit(1)

    config["active"] = account_name
    save_config(config)
    print(f"✅ Switched active account to: {account_name}")
