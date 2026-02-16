import subprocess
import click
from cli.config import get_active_account, get_token, get_linked_account
from cli.git_utils import choose_remote
from cli.git_utils import git_auth_env

@click.command(name="pull")
@click.option("--branch", default="main", help="Branch to pull from (default: main)")
@click.option("--remote", default=None, help="Remote name (default: auto-detected or 'origin')")
def pull_repo(branch, remote):
    """Pull from GitHub using the active account."""
    account = get_active_account()

    if not account:
        raise click.ClickException("No active account found. Use `ghmulti use ACCOUNT_NAME`.")

    username = account["username"]
    token = get_token(username)

    # Determine the remote to use
    linked_account_name = get_linked_account()
    actual_remote = choose_remote(linked_account_name, remote)
    if linked_account_name and actual_remote == f"origin-{linked_account_name}":
        click.echo(f"ℹ️  Using linked account remote: {actual_remote}")
    elif not remote:
        click.echo(f"ℹ️  Using default remote: {actual_remote}")

    click.echo(f"📥 Pulling from GitHub as '{username}' from remote '{actual_remote}'...")

    try:
        with git_auth_env(token=token, username=username) as env:
            subprocess.run(["git", "pull", actual_remote, branch], check=True, env=env)
        click.echo("✅ Pull successful.")
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"Git pull failed: {e}") from e
