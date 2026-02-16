import subprocess
import click

from cli.config import get_active_account, get_token, get_linked_account
from cli.git_utils import choose_remote
from cli.git_utils import git_auth_env

@click.command(name="push")
@click.option('--branch', default='main', help='Branch name to push (default: main)')
@click.option('--message', help='Commit message if staging and committing before push')
@click.option("--remote", default=None, help="Remote name (default: auto-detected or 'origin')")
def push(branch, message, remote):
    """Push to GitHub using the active account's remote."""
    account = get_active_account()

    if not account:
        raise click.ClickException("No active account found. Use `ghmulti use ACCOUNT_NAME`.")

    username = account['username']
    token = get_token(username)

    # Determine the remote to use
    linked_account_name = get_linked_account()
    actual_remote = choose_remote(linked_account_name, remote)
    if linked_account_name and actual_remote == f"origin-{linked_account_name}":
        click.echo(f"ℹ️  Using linked account remote: {actual_remote}")
    elif not remote:
        click.echo(f"ℹ️  Using default remote: {actual_remote}")

    click.echo(f"📤 Pushing as '{username}' to remote '{actual_remote}' on branch '{branch}'")

    try:
        if message:
            click.echo("📝 Committing changes...")
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", message], check=True)

        with git_auth_env(token=token, username=username) as env:
            subprocess.run(["git", "push", actual_remote, branch], check=True, env=env)
        click.echo("✅ Push successful.")
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"Git command failed: {e}") from e

if __name__ == "__main__":
    push()
