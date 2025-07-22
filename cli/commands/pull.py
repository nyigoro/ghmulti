import subprocess
import sys
import os
import json
import click

CONFIG_PATH = os.path.expanduser("~/.ghmulti.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("❌ Config file not found. Run `add` to create one.")
        sys.exit(1)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

@click.command(name="pull")
@click.option("--branch", default="main", help="Branch to pull from (default: main)")
@click.option("--remote", default="origin", help="Remote name (default: origin)")
def pull_repo(branch, remote):
    """Pull from GitHub using the active account."""
    config = load_config()
    active_name = config.get("active")

    if not active_name:
        print("❌ No active account set. Use `ghmulti use ACCOUNT_NAME`.")
        sys.exit(1)

    accounts = config.get("accounts", [])
    match = next((a for a in accounts if a["name"] == active_name), None)
    if not match:
        print(f"❌ Active account '{active_name}' not found.")
        sys.exit(1)

    username = match["username"]
    method = match.get("method", "ssh")

    print(f"📥 Pulling from GitHub as '{username}' using {method.upper()}...")

    try:
        subprocess.run(["git", "pull", remote, branch], check=True)
        print("✅ Pull successful.")
    except subprocess.CalledProcessError as e:
        print("❌ Git pull failed:", e)
        sys.exit(1)
