import os
import json
import click
import keyring

CONFIG_PATH = os.path.expanduser("~/.ghmulti.json")

@click.command(name="add")
def add_account():
    """Add a new GitHub account."""
    name = input("Account name: ").strip()
    username = input("GitHub username: ").strip()
    token = input("Personal access token: ").strip()

    if not name or not username or not token:
        print("❌ All fields are required.")
        return

    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

    if "accounts" not in config:
        config["accounts"] = []

    # Check if account with same name exists
    if any(a["name"] == name for a in config["accounts"]):
        print(f"❌ Account '{name}' already exists.")
        return

    config["accounts"].append({
        "name": name,
        "username": username,
    })
    
    keyring.set_password("ghmulti", username, token)

    if "active" not in config:
        config["active"] = name

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ Added account '{name}' and saved.")
