import os
import json
import click
import subprocess
from cli.config import load_config

PROJECT_CONFIG_FILE = ".ghmulti"

@click.command(name="link")
@click.argument("account_name")
def link_account(account_name):
    """Link a GitHub account to the current repository."""
    config = load_config()
    accounts = config.get("accounts", [])
    
    target_account = next((acc for acc in accounts if acc["name"] == account_name), None)
    if not target_account:
        click.echo(f"❌ Account '{account_name}' not found in your ghmulti config.")
        click.echo("Run `ghmulti list` to see available accounts.")
        return

    if not os.path.exists(".git"):
        click.echo("❌ This does not appear to be a git repository.")
        return

    # Create the .ghmulti project file
    project_config = {"account": account_name}
    with open(PROJECT_CONFIG_FILE, "w") as f:
        json.dump(project_config, f, indent=2)

    # Set git config locally for this repository
    subprocess.run(["git", "config", "--local", "user.name", target_account["username"]], check=True)
    subprocess.run(["git", "config", "--local", "user.email", f'{target_account["username"]}@users.noreply.github.com'], check=True)

    if "gpg_key_id" in target_account:
        subprocess.run(["git", "config", "--local", "user.signingkey", target_account["gpg_key_id"]], check=True)

    if "ssh_key_path" in target_account:
        ssh_command = f"ssh -i {os.path.expanduser(target_account['ssh_key_path'])}"
        subprocess.run(["git", "config", "--local", "core.sshCommand", ssh_command], check=True)

    click.echo(f"✅ Successfully linked account '{account_name}' to this repository.")