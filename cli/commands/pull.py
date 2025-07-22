import subprocess
import sys
import click
from cli.config import get_active_account, get_token

@click.command(name="pull")
@click.option("--branch", default="main", help="Branch to pull from (default: main)")
@click.option("--remote", default="origin", help="Remote name (default: origin)")
def pull_repo(branch, remote):
    """Pull from GitHub using the active account."""
    account = get_active_account()

    if not account:
        click.echo("❌ No active account found. Use `ghmulti use ACCOUNT_NAME`.")
        sys.exit(1)

    username = account["username"]
    token = get_token(username)

    click.echo(f"📥 Pulling from GitHub as '{username}'...")

    try:
        subprocess.run(["git", "pull", remote, branch], check=True, env={"GIT_ASKPASS": "echo", "GIT_USERNAME": username, "GIT_PASSWORD": token})
        click.echo("✅ Pull successful.")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Git pull failed: {e}")
        sys.exit(1)
