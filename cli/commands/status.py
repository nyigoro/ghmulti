# cli/commands/status.py
import os
import click
import subprocess
from cli.config import get_active_account, get_linked_account, get_token

@click.command(name="status")
def status():
    """Show the current ghmulti status and active account."""
    click.echo("🔎 Checking ghmulti status...")

    linked_account = get_linked_account()
    active_account = get_active_account()

    if linked_account:
        click.echo(f"🔗 Repository linked to: '{linked_account}' (via .ghmulti)")
    
    if not active_account:
        click.echo("❌ No active account configured. Run `ghmulti use` or `ghmulti link`.")
        return

    click.echo(f"👤 Active account: '{active_account['name']}' ({active_account['username']})")

    # Check git config user.name and user.email
    try:
        git_user = subprocess.check_output(["git", "config", "user.name"]).decode().strip()
        git_email = subprocess.check_output(["git", "config", "user.email"]).decode().strip()
        click.echo(f"✒️  Git config user: {git_user} <{git_email}> ")
        if git_user != active_account['username']:
            click.echo("    ⚠️  Warning: Git user.name does not match the active account username.")
    except subprocess.CalledProcessError:
        click.echo("    ⚠️  Warning: Could not read git user config.")

    # Check git config user.signingkey
    try:
        git_signingkey = subprocess.check_output(["git", "config", "user.signingkey"]).decode().strip()
        click.echo(f"✍️  Git signing key: {git_signingkey}")
        if active_account.get('gpg_key_id') and git_signingkey != active_account['gpg_key_id']:
            click.echo(f"    ⚠️  Warning: Git signing key does not match active account's GPG ID ({active_account['gpg_key_id']}).")
        elif not active_account.get('gpg_key_id'):
            click.echo("    ℹ️  Active account has no GPG ID configured.")
    except subprocess.CalledProcessError:
        click.echo("    ℹ️  Git signing key not configured.")

    # Check git config core.sshCommand
    try:
        git_ssh_command = subprocess.check_output(["git", "config", "core.sshCommand"]).decode().strip()
        click.echo(f"🔑 Git SSH command: {git_ssh_command}")
        if active_account.get('ssh_key_path') and not git_ssh_command.endswith(os.path.expanduser(active_account['ssh_key_path'])):\
            click.echo(f"    ⚠️  Warning: Git SSH command does not match active account's SSH key path ({active_account['ssh_key_path']}).")
        elif not active_account.get('ssh_key_path'):
            click.echo("    ℹ️  Active account has no SSH key path configured.")
    except subprocess.CalledProcessError:
        click.echo("    ℹ️  Git SSH command not configured.")

    # Validate token
    token = get_token(active_account['username'])
    if not token:
        click.echo("❌ Token not found for the active account in keychain.")
        return

    click.echo("🔑 Verifying token with GitHub...")
    try:
        command = ["curl", "-sS", "-H", f"Authorization: token {token}", "https://api.github.com/user", "-o", os.devnull]
        subprocess.run(command, check=True)
        click.echo("✅ Token is valid and has access to user data.")
    except subprocess.CalledProcessError:
        click.echo("❌ Token is invalid or expired. Please update it using `ghmulti add`.")
