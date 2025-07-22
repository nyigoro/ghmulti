import subprocess
import sys
import click
import os
from cli.config import get_active_account, get_token, get_linked_account

def run(cmd, env=None, shell=False):
    print(f"🛠️  Running: {cmd}")
    result = subprocess.run(cmd, shell=shell, env=env)
    if result.returncode != 0:
        print("❌ Command failed.")
        sys.exit(result.returncode)

@click.command(name="push")
@click.option('--branch', default='main', help='Branch name to push (default: main)')
@click.option('--message', help='Commit message if staging and committing before push')
@click.option("--remote", default=None, help="Remote name (default: auto-detected or 'origin')")
def push(branch, message, remote):
    """Push to GitHub using the active account's remote."""
    account = get_active_account()

    if not account:
        click.echo("❌ No active account found. Use `ghmulti use ACCOUNT_NAME`.")
        sys.exit(1)

    username = account['username']
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

    click.echo(f"📤 Pushing as '{username}' to remote '{actual_remote}' on branch '{branch}'")

    if message:
        click.echo("📝 Committing changes...")
        run(["git", "add", "."])
        run(["git", "commit", "-m", message])

    # Use GIT_ASKPASS for token authentication
    env = os.environ.copy()
    if token:
        env["GIT_ASKPASS"] = "echo"
        env["GIT_USERNAME"] = username
        env["GIT_PASSWORD"] = token

    run(["git", "push", actual_remote, branch], env=env)
    click.echo("✅ Push successful.")

if __name__ == "__main__":
    push()
