import os
import json
import click
import keyring
import sys

CONFIG_PATH = os.path.expanduser("~/.ghmulti.json")

@click.command(name="add")
def add_account():
    """Add a new GitHub account."""
    name = input("Account name: ").strip()
    username = input("GitHub username: ").strip()
    token = input("Personal access token (optional, leave blank for SSH): ").strip()
    gpg_key_id = input("GPG Signing Key ID (optional): ").strip()
    ssh_key_path = input("SSH Key Path (e.g., ~/.ssh/id_rsa_github_personal, optional): ").strip()

    if not name or not username:
        print("❌ Account name and GitHub username are required.")
        sys.exit(1)

    if not token and not ssh_key_path:
        print("❌ Either a Personal Access Token or an SSH Key Path is required.")
        sys.exit(1)

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

    new_account = {
        "name": name,
        "username": username,
    }
    if gpg_key_id:
        new_account["gpg_key_id"] = gpg_key_id
    if ssh_key_path:
        new_account["ssh_key_path"] = ssh_key_path

    config["accounts"].append(new_account)
    
    if token:
        keyring.set_password("ghmulti", username, token)

    if "active" not in config:
        config["active"] = name

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ Added account '{name}' and saved.")
