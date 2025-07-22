import os
import json
import click

CONFIG_PATH = os.path.expanduser("~/.ghmulti.json")

@click.command(name="list")
def list_accounts():
    """List all configured GitHub accounts."""
    if not os.path.exists(CONFIG_PATH):
        print("❌ No config file found. Run `add` to add accounts.")
        return

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    accounts = config.get("accounts", [])
    active = config.get("active")

    if not accounts:
        print("ℹ️  No accounts configured.")
        return

    print("📘 Configured GitHub accounts:")
    for acc in accounts:
        name = acc.get("name", "<no-name>")
        username = acc.get("username", "<no-username>")
        marker = "👉" if name == active else "  "
        print(f"{marker} {name} ({username})")
