import click

from cli.config import get_linked_account
from cli.config import load_config
from cli.config import save_config
from cli.config import set_linked_account


@click.command(name="rename")
@click.argument("old_name")
@click.argument("new_name")
def rename_account(old_name, new_name):
    """Rename an account alias."""
    if old_name == new_name:
        raise click.ClickException("Old and new account names are the same.")

    data = load_config()
    accounts = data.get("accounts", [])
    target = next((account for account in accounts if account["name"] == old_name), None)
    if not target:
        raise click.ClickException(f"Account '{old_name}' not found.")

    if any(account["name"] == new_name for account in accounts):
        raise click.ClickException(f"Account '{new_name}' already exists.")

    target["name"] = new_name
    if data.get("active") == old_name:
        data["active"] = new_name
    save_config(data)

    if get_linked_account() == old_name:
        set_linked_account(new_name)

    click.echo(f"✅ Renamed account '{old_name}' to '{new_name}'.")
