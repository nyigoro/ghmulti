import subprocess
import click
import os
import re

def detect_remote_type(url):
    if url.startswith("git@"):
        return "ssh"
    if url.startswith("https://") or url.startswith("http://"):
        return "https"
    return "unknown"

def test_ssh_connectivity(url):
    """Try SSHing to the host to test connectivity."""
    try:
        host = url.split("@")[1].split(":")[0]
        subprocess.check_output(["ssh", "-T", f"git@{host}"], stderr=subprocess.STDOUT, timeout=5)
        return True
    except subprocess.CalledProcessError as e:
        return b"successfully authenticated" in e.output.lower()
    except Exception:
        return False

def test_https_connectivity(url):
    """Try a simple ls-remote on the HTTPS URL."""
    try:
        subprocess.check_output(["git", "ls-remote", url], stderr=subprocess.DEVNULL, timeout=5)
        return True
    except Exception:
        return False

@click.command(name="check-remote")
def check_remote():
    """Check connectivity to all Git remotes (SSH or HTTPS)."""
    if not os.path.exists(".git"):
        click.echo("❌ Not a Git repository.")
        return

    try:
        remotes_output = subprocess.check_output(["git", "remote", "-v"], text=True).strip().splitlines()
    except subprocess.CalledProcessError:
        click.echo("❌ Failed to list remotes.")
        return

    if not remotes_output:
        click.echo("ℹ️  No remotes configured.")
        return

    seen = set()
    click.echo("🔍 Checking connectivity to remotes...\n")

    for line in remotes_output:
        match = re.match(r"(\S+)\s+(\S+)\s+\((fetch|push)\)", line)
        if not match:
            continue

        name, url, _ = match.groups()
        if (name, url) in seen:
            continue
        seen.add((name, url))

        rtype = detect_remote_type(url)
        status = "❓ Unknown"
        if rtype == "ssh":
            status = "✅ SSH OK" if test_ssh_connectivity(url) else "❌ SSH Failed"
        elif rtype == "https":
            status = "✅ HTTPS OK" if test_https_connectivity(url) else "❌ HTTPS Failed"

        click.echo(f"• {name} → {url} [{status}]")

