import click
from .list import list_accounts
from .add import add_account
from .use import use_account
from .push import cli as push_command
from .remote import cli as remote_command
from .pull import pull_repo
from .list_remote import list_remotes
from .check_remote import check_remote
from .link import link_account
from .status import status
from .clone import clone_repo

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
cli.add_command(pull_repo)
cli.add_command(list_remotes)
cli.add_command(check_remote)
cli.add_command(link_account)
cli.add_command(status)
cli.add_command(clone_repo)

if __name__ == "__main__":
    cli()
