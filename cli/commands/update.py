import click

from cli.config import delete_token
from cli.config import get_token
from cli.config import load_config
from cli.config import save_config
from cli.config import set_token


@click.command(name="update")
@click.argument("account_name")
@click.option("--username", default=None, help="Update GitHub username.")
@click.option("--gpg-key-id", default=None, help="Update GPG key ID (pass empty string to clear).")
@click.option("--ssh-key-path", default=None, help="Update SSH key path (pass empty string to clear).")
@click.option("--token", default=None, help="Set a new GitHub token.")
@click.option("--clear-token", is_flag=True, help="Delete token from keyring.")
@click.option("--set-active", is_flag=True, help="Set this account as the global active account.")
def update_account(account_name, username, gpg_key_id, ssh_key_path, token, clear_token, set_active):
    """Update account details."""
    if token and clear_token:
        raise click.ClickException("Use either --token or --clear-token, not both.")

    data = load_config()
    target = next((account for account in data.get("accounts", []) if account["name"] == account_name), None)
    if not target:
        raise click.ClickException(f"Account '{account_name}' not found.")

    old_username = target["username"]
    changed = False

    if username:
        target["username"] = username.strip()
        changed = True

    if gpg_key_id is not None:
        clean_gpg = gpg_key_id.strip()
        if clean_gpg:
            target["gpg_key_id"] = clean_gpg
        else:
            target.pop("gpg_key_id", None)
        changed = True

    if ssh_key_path is not None:
        clean_ssh = ssh_key_path.strip()
        if clean_ssh:
            target["ssh_key_path"] = clean_ssh
        else:
            target.pop("ssh_key_path", None)
        changed = True

    if set_active:
        data["active"] = target["name"]
        changed = True

    if old_username != target["username"]:
        existing_old_token = get_token(old_username)
        if existing_old_token and token is None and not clear_token:
            set_token(target["username"], existing_old_token)
        delete_token(old_username)

    if token is not None:
        token_value = token.strip()
        if token_value:
            set_token(target["username"], token_value)
            changed = True

    if clear_token:
        delete_token(target["username"])
        changed = True

    if not changed:
        click.echo("No changes requested.")
        return

    save_config(data)
    click.echo(f"✅ Updated account '{account_name}'.")
