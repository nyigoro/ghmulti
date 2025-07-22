import click
from .list import list_accounts
from .add import add_account
from .use import use_account
from .push import cli as push_command
from .remote import cli as remote_command
from .pull import cli as pull_command

@click.group()
def cli():
    """ghmulti CLI – Manage multiple GitHub accounts."""
    pass

# Add subcommands
cli.add_command(add_account)
cli.add_command(list_accounts)
cli.add_command(use_account)
cli.add_command(push_command, name="push")
cli.add_command(remote_command, name="remote")
cli.add_command(pull_command, name="pull")

if __name__ == "__main__":
    cli()
