# ghmulti/cli.py

import os
import json
import click
import sys

CONFIG_PATH = os.path.expanduser("~/.ghmulti.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"accounts": [], "active": None}


@click.group()
def cli():
    """Manage multiple GitHub accounts and Git identities."""
    pass


@cli.command(name="list")
def list_accounts():
    """List all configured accounts."""
    config = load_config()
    if not config["accounts"]:
        click.echo("No accounts configured.")
        return

    for account in config["accounts"]:
        name = account["name"]
        email = account["email"]
        active = " (active)" if config["active"] == name else ""
        click.echo(f"- {name} <{email}>{active}")


@cli.command()
@click.argument("name")
def use(name):
    """Set an account as active by name."""
    config = load_config()
    if any(acc["name"] == name for acc in config["accounts"]):
        config["active"] = name
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        click.echo(f"✅ Active account set to '{name}'")
    else:
        click.echo(f"❌ No account named '{name}' found.")


@cli.command()
def add():
    """Add a new GitHub account configuration."""
    config = load_config()

    name = input("Account name (e.g. personal, work): ").strip()
    email = input("Git email: ").strip()
    auth_type = input("Auth type (ssh/token): ").strip().lower()

    token = None
    if auth_type == "token":
        token = input("GitHub token (PAT): ").strip()

    new_account = {
        "name": name,
        "email": email,
        "auth": {
            "type": auth_type,
            "token": token
        }
    }

    config["accounts"].append(new_account)
    if config["active"] is None:
        config["active"] = name

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    click.echo(f"✅ Added account '{name}'")


@cli.command()
def apply():
    """Apply Git identity config for the active account."""
    config = load_config()
    active_name = config.get("active")

    if not active_name:
        click.echo("❌ No active account set. Use 'use' command to set one.")
        return

    account = next((acc for acc in config["accounts"] if acc["name"] == active_name), None)
    if not account:
        click.echo(f"❌ Active account '{active_name}' not found.")
        return

    email = account["email"]
    name = account["name"]

    click.echo(f"🔧 Setting Git identity for account: {name} ({email})")

    os.system(f'git config user.email "{email}"')
    os.system(f'git config user.name "{name}"')

    if account["auth"]["type"] == "token":
        token = account["auth"]["token"]
        click.echo("💡 If needed, you can set your remote like:")
        click.echo(f"   git remote set-url origin https://{token}@github.com/USERNAME/REPO.git")

    click.echo("✅ Git config applied for this repo.")


if __name__ == "__main__":
    cli()
