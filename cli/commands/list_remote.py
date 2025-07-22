import subprocess
import click
import os
import re

def get_current_branch():
    """Get the name of the currently checked-out Git branch."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        return None

def get_branch_remotes():
    """
    Returns a dictionary mapping each local branch to its tracking remote.
    Example: { "main": "origin" }
    """
    try:
        output = subprocess.check_output(["git", "branch", "-vv"], text=True).strip().splitlines()
    except subprocess.CalledProcessError:
        return {}

    tracking = {}
    for line in output:
        match = re.match(r"[\*\s]+\s*(\S+)\s+[a-f0-9]+\s+\[([^\]]+)\]", line)
        if match:
            branch, remote_ref = match.groups()
            remote = remote_ref.split("/")[0]
            tracking[branch] = remote
    return tracking

def detect_remote_type(url):
    """Return an emoji describing the remote type."""
    if url.startswith("git@"):
        return "🔒 SSH"
    if url.startswith("https://"):
        return "🌐 HTTPS"
    if url.startswith("http://"):
        return "⚠️ Insecure HTTP"
    return "❓ Unknown"

@click.command(name="list-remote")
@click.option("--all-branches", is_flag=True, help="Show tracking remotes for all branches.")
def list_remotes(all_branches):
    """
    List Git remotes and their type.
    Use --all-branches to show tracked remotes for all local branches.
    """
    if not os.path.exists(".git"):
        click.echo("❌ Not a Git repository.")
        return

    current_branch = get_current_branch()
    tracking_map = get_branch_remotes()

    try:
        remotes_output = subprocess.check_output(["git", "remote", "-v"], text=True).strip().splitlines()
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to list remotes: {e}")
        return

    if not remotes_output:
        click.echo("ℹ️  No remotes configured.")
        return

    click.echo(f"🔗 Git Remotes (current branch: {current_branch})\n")

    seen = set()
    for line in remotes_output:
        match = re.match(r"(\S+)\s+(\S+)\s+\((fetch|push)\)", line)
        if not match:
            continue
        name, url, _ = match.groups()

        if (name, url) in seen:
            continue
        seen.add((name, url))

        remote_type = detect_remote_type(url)
        is_default = name == tracking_map.get(current_branch)
        default_marker = "✔ current branch default" if is_default else ""

        click.echo(f"• {name} → {url} [{remote_type}] {default_marker}")

    if all_branches:
        click.echo("\n📦 Tracked Remotes for All Branches:")
        for branch, remote in tracking_map.items():
            marker = "← current" if branch == current_branch else ""
            click.echo(f"• {branch} → {remote} {marker}")
