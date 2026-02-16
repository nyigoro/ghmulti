import re
import subprocess

import click


def _parse_remotes() -> dict[str, str]:
    remotes: dict[str, str] = {}
    try:
        output = subprocess.check_output(["git", "remote", "-v"], text=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(f"Failed to list git remotes: {exc}") from exc

    for line in output.strip().splitlines():
        match = re.match(r"(\S+)\s+(\S+)\s+\((fetch|push)\)", line.strip())
        if not match:
            continue
        name, url, _ = match.groups()
        remotes[name] = url
    return remotes


def _check_ssh_host(url: str) -> bool:
    if "@" not in url or ":" not in url:
        return False
    host = url.split(":", 1)[0]
    try:
        result = subprocess.run(
            ["ssh", "-T", host],
            capture_output=True,
            text=True
        )
        # GitHub commonly returns exit code 1 for successful auth without shell access.
        return result.returncode in (0, 1)
    except OSError:
        return False


@click.command("check-remote")
def check_remote():
    """Check connection status for all Git remotes."""
    click.echo("🔍 Checking connectivity to remotes...\n")
    remotes = _parse_remotes()
    if not remotes:
        click.echo("ℹ️  No remotes configured.")
        return

    for name, url in remotes.items():
        if url.startswith("https://"):
            status = "✅ HTTPS configured"
        elif url.startswith("http://"):
            status = "⚠️ Insecure HTTP configured"
        elif url.startswith("git@"):
            status = "✅ SSH reachable" if _check_ssh_host(url) else "❌ SSH check failed"
        else:
            status = "❓ Unknown protocol"

        click.echo(f"• {name} → {url} [{status}]")
