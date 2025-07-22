# ghmulti/pull.py

import click
import subprocess

@click.command()
@click.option('--account', required=True, help='GitHub account name to use')
@click.option('--branch', default='main', help='Branch to pull (default: main)')
def cli(account, branch):
    """Pull from a remote using the specified GitHub account."""
    try:
        click.echo(f"📥 Pulling from remote for account '{account}' on branch '{branch}'...")
        subprocess.run(["git", "pull", "origin", branch], check=True)
        click.echo("✅ Pull complete.")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Pull failed: {e}", err=True)
