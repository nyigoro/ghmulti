import click
from .list import list_accounts
from .add import add_account
from .use import use_account
from .push import push
from .remote import remote
from .pull import pull_repo
from .list_remote import list_remotes
from .check_remote import check_remote
from .link import link_account
from .status import status
from .clone import clone_repo
from .remove import remove_account
from .rename import rename_account
from .update import update_account
from .doctor import doctor
from .unlink import unlink_account

@click.group()
def cli():
    """ghmulti CLI – Manage multiple GitHub accounts."""
    pass


@click.group()
def account():
    """Account management shortcuts."""
    pass


# account subcommands mirror top-level commands for discoverability.
account.add_command(add_account, name="add")
account.add_command(list_accounts, name="list")
account.add_command(use_account, name="use")
account.add_command(update_account, name="update")
account.add_command(remove_account, name="remove")
account.add_command(rename_account, name="rename")

# Add subcommands
cli.add_command(add_account)
cli.add_command(list_accounts)
cli.add_command(use_account)
cli.add_command(push, name="push")
cli.add_command(remote, name="remote")
cli.add_command(pull_repo)
cli.add_command(list_remotes)
cli.add_command(check_remote)
cli.add_command(link_account)
cli.add_command(status)
cli.add_command(clone_repo)
cli.add_command(remove_account)
cli.add_command(rename_account)
cli.add_command(update_account)
cli.add_command(doctor)
cli.add_command(account)
cli.add_command(unlink_account)

if __name__ == "__main__":
    cli()
