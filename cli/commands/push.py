import subprocess
import sys
import click
from cli.config import get_active_account, get_token

def run(cmd, env=None):
    print(f"🛠️  Running: {cmd}")
    result = subprocess.run(cmd, shell=True, env=env)
    if result.returncode != 0:
        print("❌ Command failed.")
        sys.exit(result.returncode)

@click.command(name="push")
@click.option('--branch', default='main', help='Branch name to push (default: main)')
@click.option('--message', help='Commit message if staging and committing before push')
def push(branch, message):
    """Push to GitHub using the active account's remote."""
    account = get_active_account()

    if not account:
        click.echo("❌ No active account found. Use `ghmulti use ACCOUNT_NAME`.")
        sys.exit(1)

    username = account['username']
    token = get_token(username)
    remote_name = f"origin-{account['name']}"

    click.echo(f"📤 Pushing as '{username}' to remote '{remote_name}' on branch '{branch}'")

    if message:
        click.echo("📝 Committing changes...")
        run("git add .")
        run(f'git commit -m "{message}"')

    run(f"git push {remote_name} {branch}", env={"GIT_ASKPASS": "echo", "GIT_USERNAME": username, "GIT_PASSWORD": token})
    click.echo("✅ Push successful.")

if __name__ == "__main__":
    push()
