import click

from cli.config import clear_linked_account
from cli.config import delete_token
from cli.config import get_linked_account
from cli.config import load_config
from cli.config import save_config


@click.command(name="remove")
@click.argument("account_name")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def remove_account(account_name, yes):
    """Remove an account from ghmulti config."""
    data = load_config()
    accounts = data.get("accounts", [])
    target = next((account for account in accounts if account["name"] == account_name), None)
    if not target:
        raise click.ClickException(f"Account '{account_name}' not found.")

    if not yes and not click.confirm(f"Remove account '{account_name}'?"):
        click.echo("Cancelled.")
        return

    data["accounts"] = [account for account in accounts if account["name"] != account_name]

    if data.get("active") == account_name:
        data["active"] = data["accounts"][0]["name"] if data["accounts"] else None

    save_config(data)
    delete_token(target["username"])

    if get_linked_account() == account_name:
        clear_linked_account()
        click.echo("ℹ️  Current repository was linked to the removed account and has been unlinked.")

    click.echo(f"✅ Removed account '{account_name}'.")
