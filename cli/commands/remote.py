import subprocess

import click


def _run_git(args: list[str]) -> None:
    try:
        subprocess.run(["git", *args], check=True)
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(f"Git command failed: git {' '.join(args)} ({exc})") from exc


@click.group("remote")
def remote():
    """Manage Git remotes per GitHub account."""
    pass


@remote.command("add")
@click.option("--account", required=True, help="GitHub account name (e.g., nyigoro)")
@click.option("--url", required=True, help="Remote URL (HTTPS or SSH)")
def remote_add(account, url):
    remote_name = f"origin-{account}"
    click.echo(f"➕ Adding remote '{remote_name}' → {url}")
    _run_git(["remote", "add", remote_name, url])


@remote.command("remove")
@click.option("--account", required=True, help="GitHub account name")
def remote_remove(account):
    remote_name = f"origin-{account}"
    click.echo(f"❌ Removing remote '{remote_name}'")
    _run_git(["remote", "remove", remote_name])
