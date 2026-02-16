import os
import subprocess

import click
import inquirer

from cli.config import get_account_by_name
from cli.config import get_accounts
from cli.config import get_token
from cli.git_utils import git_auth_env
from cli.commands.link import link_account_logic


def _derive_repo_directory(repo_url: str) -> str:
    repo_name = repo_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    return repo_name


def _choose_account_interactively(prompt: str) -> str:
    accounts = get_accounts()
    if not accounts:
        raise click.ClickException("No accounts configured. Run `ghmulti add` first.")

    question = [
        inquirer.List(
            "account",
            message=prompt,
            choices=[acc["name"] for acc in accounts],
            carousel=True
        )
    ]
    answers = inquirer.prompt(question)
    if not answers or "account" not in answers:
        raise click.ClickException("No account selected.")
    return answers["account"]


@click.command(name="clone")
@click.argument("repo_url")
@click.option("--account", "account_name", default=None, help="Account name to use for clone/linking.")
@click.option("--link/--no-link", "should_link", default=None, help="Link the cloned repository immediately.")
def clone_repo(repo_url, account_name, should_link):
    """Clone a GitHub repository and optionally link it to a ghmulti account."""
    click.echo(f"Starting clone of {repo_url}...")
    account_to_use = get_account_by_name(account_name) if account_name else None
    if account_name and not account_to_use:
        raise click.ClickException(f"Account '{account_name}' not found in ghmulti config.")

    token = get_token(account_to_use["username"]) if account_to_use else None
    if account_to_use and token:
        click.echo(f"ℹ️  Attempting to clone using token for {account_to_use['username']}")

    try:
        with git_auth_env(token=token, username=account_to_use["username"] if account_to_use else None) as env:
            subprocess.run(["git", "clone", repo_url], check=True, env=env)
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(f"Git clone failed: {exc}") from exc

    repo_dir = _derive_repo_directory(repo_url)
    click.echo(f"✅ Successfully cloned {repo_url} into {repo_dir}/")

    if should_link is None:
        if account_name:
            should_link = True
        else:
            should_link = click.confirm("Do you want to link an account to this repository now?", default=False)

    if not should_link:
        click.echo("ℹ️  No account specified for linking. You can link one manually:")
        click.echo("    `ghmulti link <account_name>`")
        return

    selected_account_name = account_name or _choose_account_interactively(
        "Select account to link to the cloned repository"
    )
    click.echo(f"🔗 Linking repository to account '{selected_account_name}'...")
    try:
        link_account_logic(selected_account_name, repo_path=repo_dir)
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(f"Failed to link cloned repository: {exc}") from exc
    click.echo(f"✅ Repository linked to '{selected_account_name}'.")
