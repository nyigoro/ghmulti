import json
import os

import click

from cli.config import clear_linked_account
from cli.config import get_linked_account
from cli.config import unset_git_config_value


@click.command(name="unlink")
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
@click.option(
    "--reset-local-git",
    is_flag=True,
    help="Also unset local git identity fields (user.name/user.email/user.signingkey/core.sshCommand)."
)
def unlink_account(json_output, reset_local_git):
    """Unlink the current repository from a ghmulti account."""
    repo_path = "."
    if not os.path.exists(os.path.join(repo_path, ".git")):
        raise click.ClickException("This does not appear to be a git repository.")

    linked_account = get_linked_account(repo_path=repo_path)
    clear_linked_account(repo_path=repo_path)

    if reset_local_git:
        unset_git_config_value("--local", "user.name", cwd=repo_path)
        unset_git_config_value("--local", "user.email", cwd=repo_path)
        unset_git_config_value("--local", "user.signingkey", cwd=repo_path)
        unset_git_config_value("--local", "core.sshCommand", cwd=repo_path)

    if json_output:
        click.echo(json.dumps({
            "previously_linked_account": linked_account,
            "unlinked": True,
            "reset_local_git": reset_local_git
        }, indent=2))
        return

    if linked_account:
        click.echo(f"✅ Unlinked repository from account '{linked_account}'.")
    else:
        click.echo("ℹ️  Repository was not linked to an account.")

    if reset_local_git:
        click.echo("🧹 Local git identity fields were reset.")
