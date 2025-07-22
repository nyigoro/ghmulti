import os
import subprocess
import sys
import click
from cli.config import get_active_account, get_token, get_linked_account

@click.command(name="pull")
@click.option("--branch", default="main", help="Branch to pull from (default: main)")
@click.option("--remote", default=None, help="Remote name (default: auto-detected or 'origin')")
def pull_repo(branch, remote):
    """Pull from GitHub using the active account."""
    account = get_active_account()

    if not account:
        click.echo("❌ No active account found. Use `ghmulti use ACCOUNT_NAME`.")
        sys.exit(1)

    username = account["username"]
    token = get_token(username)

    # Determine the remote to use
    actual_remote = remote
    if not actual_remote:
        linked_account_name = get_linked_account()
        if linked_account_name:
            # Check if a remote named origin-{linked_account_name} exists
            try:
                remotes_output = subprocess.check_output(["git", "remote"], stderr=subprocess.PIPE).decode().splitlines()
                if f"origin-{linked_account_name}" in remotes_output:
                    actual_remote = f"origin-{linked_account_name}"
                    click.echo(f"ℹ️  Using linked account remote: {actual_remote}")
            except subprocess.CalledProcessError:
                pass # Ignore if git remote fails
        
        if not actual_remote:
            actual_remote = "origin"
            click.echo(f"ℹ️  Using default remote: {actual_remote}")

    click.echo(f"📥 Pulling from GitHub as '{username}' from remote '{actual_remote}'...")

    try:
        # Use GIT_ASKPASS for token authentication
        env = os.environ.copy()
        if token:
            env["GIT_ASKPASS"] = "echo"
            env["GIT_USERNAME"] = username
            env["GIT_PASSWORD"] = token
        
        subprocess.run(["git", "pull", actual_remote, branch], check=True, env=env)
        click.echo("✅ Pull successful.")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Git pull failed: {e}")
        sys.exit(1)
