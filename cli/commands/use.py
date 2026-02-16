import os
import json
import click
import subprocess
import inquirer
from cli.config import get_account_by_name
from cli.config import load_config
from cli.config import save_config


def switch_account_logic(account_name):
    config = load_config()
    match = get_account_by_name(account_name)

    if not match:
        raise click.ClickException(f"No account named '{account_name}' found.")

    config["active"] = account_name
    save_config(config)

    try:
        # Configure git user globally
        subprocess.run(["git", "config", "--global", "user.name", match["username"]], check=True)
        subprocess.run(["git", "config", "--global", "user.email", f'{match["username"]}@users.noreply.github.com'], check=True)
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(f"Failed to set global git identity: {exc}") from exc

    # Configure GPG signing key if provided
    gpg_key_id = match.get("gpg_key_id")
    if gpg_key_id:
        subprocess.run(["git", "config", "--global", "user.signingkey", gpg_key_id], check=True)
        click.echo(f"✅ Global Git GPG signing key set to: {gpg_key_id}")
    else:
        # Unset if not provided
        subprocess.run(["git", "config", "--global", "--unset-all", "user.signingkey"], check=False)
        click.echo("ℹ️  Global Git GPG signing key unset.")

    # Configure SSH command if SSH key path is provided
    ssh_key_path = match.get("ssh_key_path")
    if ssh_key_path:
        # Use ssh-agent for better security and management
        ssh_command = f"ssh -i {os.path.expanduser(ssh_key_path)}"
        subprocess.run(["git", "config", "--global", "core.sshCommand", ssh_command], check=True)
        click.echo(f"✅ Global Git SSH command set to: {ssh_command}")
    else:
        # Unset if not provided
        subprocess.run(["git", "config", "--global", "--unset-all", "core.sshCommand"], check=False)
        click.echo("ℹ️  Global Git SSH command unset.")

    return match

@click.command(name="use")
@click.argument("account_name", required=False)
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
def use_account(account_name, json_output):
    """
    Switch the global active GitHub account.

    If ACCOUNT_NAME is not provided, an interactive menu will be shown.
    """
    if account_name:
        selected_account = account_name
    else:
        config = load_config()
        accounts = config.get("accounts", [])
        if not accounts:
            if json_output:
                click.echo(json.dumps({"selected": None, "message": "No accounts configured."}, indent=2))
            else:
                click.echo("ℹ️  No accounts configured. Run `ghmulti add` to add one.")
            return

        account_choices = [acc["name"] for acc in accounts]

        questions = [
            inquirer.List(
                "account",
                message="Which account do you want to use globally?",
                choices=account_choices,
                carousel=True,
            ),
        ]

        answers = inquirer.prompt(questions)
        if not answers or "account" not in answers:
            raise click.ClickException("No account selected.")
        selected_account = answers["account"]

    selected = switch_account_logic(selected_account)

    if json_output:
        click.echo(json.dumps({
            "selected": selected.get("name"),
            "username": selected.get("username")
        }, indent=2))
    else:
        click.echo(f"✅ Switched global active account to: {selected_account}")
