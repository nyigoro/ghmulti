import json
import os
import subprocess

import click
import inquirer

from cli.config import get_account_by_name
from cli.config import get_accounts
from cli.config import set_linked_account
from cli.config import unset_git_config_value


def link_account_logic(account_name: str, repo_path: str = ".") -> dict:
    target_account = get_account_by_name(account_name)
    if not target_account:
        raise click.ClickException(f"Account '{account_name}' not found in your ghmulti config.")

    if not os.path.exists(os.path.join(repo_path, ".git")):
        raise click.ClickException("This does not appear to be a git repository.")

    set_linked_account(account_name, repo_path=repo_path)

    # Set git config locally for this repository
    subprocess.run(["git", "config", "--local", "user.name", target_account["username"]], check=True, cwd=repo_path)
    subprocess.run(
        ["git", "config", "--local", "user.email", f'{target_account["username"]}@users.noreply.github.com'],
        check=True,
        cwd=repo_path
    )

    if "gpg_key_id" in target_account:
        subprocess.run(["git", "config", "--local", "user.signingkey", target_account["gpg_key_id"]], check=True, cwd=repo_path)
    else:
        unset_git_config_value("--local", "user.signingkey", cwd=repo_path)

    if "ssh_key_path" in target_account:
        expanded_key = os.path.expanduser(target_account["ssh_key_path"])
        subprocess.run(["git", "config", "--local", "core.sshCommand", f"ssh -i {expanded_key}"], check=True, cwd=repo_path)
    else:
        unset_git_config_value("--local", "core.sshCommand", cwd=repo_path)

    return target_account


def _choose_account_interactively() -> str:
    accounts = get_accounts()
    if not accounts:
        raise click.ClickException("No accounts configured. Run `ghmulti add` first.")

    question = [
        inquirer.List(
            "account",
            message="Select account to link to this repository",
            choices=[acc["name"] for acc in accounts],
            carousel=True
        )
    ]
    answers = inquirer.prompt(question)
    if not answers or "account" not in answers:
        raise click.ClickException("No account selected.")
    return answers["account"]


@click.command(name="link")
@click.argument("account_name", required=False)
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
def link_account(account_name, json_output):
    """Link a GitHub account to the current repository."""
    selected_name = account_name or _choose_account_interactively()
    account = link_account_logic(selected_name)

    if json_output:
        click.echo(json.dumps({
            "linked_account": account["name"],
            "username": account["username"]
        }, indent=2))
    else:
        click.echo(f"✅ Successfully linked account '{selected_name}' to this repository.")
