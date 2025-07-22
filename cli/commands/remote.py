import subprocess
import sys
import click

def run(cmd):
    print(f"🔧 {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        sys.exit(result.returncode)

@click.group("remote")
def remote():
    """Manage Git remotes per GitHub account."""
    pass

@remote.command("add")
@click.option('--account', required=True, help='GitHub account name (e.g., nyigoro)')
@click.option('--url', required=True, help='Remote URL (HTTPS or SSH)')
def remote_add(account, url):
    remote_name = f"origin-{account}"
    print(f"➕ Adding remote '{remote_name}' → {url}")
    run(f"git remote add {remote_name} {url}")

@remote.command("remove")
@click.option('--account', required=True, help='GitHub account name')
def remote_remove(account):
    remote_name = f"origin-{account}"
    print(f"❌ Removing remote '{remote_name}'")
    run(f"git remote remove {remote_name}")
