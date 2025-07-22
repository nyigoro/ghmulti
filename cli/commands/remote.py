import subprocess
import sys
import click

def run(cmd):
    print(f"🔧 {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        sys.exit(result.returncode)

@click.group()
def cli():
    """Manage Git remotes by GitHub account."""
    pass

@cli.command("add")
@click.option('--account', required=True, help='GitHub account name (e.g., nyigoro)')
@click.option('--url', required=True, help='Git remote URL (e.g., git@github.com:user/repo.git)')
def remote_add(account, url):
    """Add a new Git remote for an account."""
    remote_name = f"origin-{account}"
    print(f"➕ Adding remote '{remote_name}' → {url}")
    run(f"git remote add {remote_name} {url}")

@cli.command("remove")
@click.option('--account', required=True, help='GitHub account name to remove')
def remote_remove(account):
    """Remove a Git remote for an account."""
    remote_name = f"origin-{account}"
    print(f"❌ Removing remote '{remote_name}'")
    run(f"git remote remove {remote_name}")

if __name__ == "__main__":
    cli()
