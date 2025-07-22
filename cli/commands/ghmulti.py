import click
from .list import list_accounts
from .add import add_account
from .use import use_account

@click.group()
def cli():
    """ghmulti CLI – Manage multiple GitHub accounts."""
    pass

cli.add_command(add_account)
cli.add_command(list_accounts)
cli.add_command(use_account)

if __name__ == "__main__":
    cli()
