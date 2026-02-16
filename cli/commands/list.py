import json
import click

from cli.config import load_config


@click.command(name="list")
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
def list_accounts(json_output):
    """List all configured GitHub accounts."""
    config = load_config()
    accounts = config.get("accounts", [])
    active = config.get("active")

    if json_output:
        payload = {
            "accounts": accounts,
            "active": active
        }
        click.echo(json.dumps(payload, indent=2))
        return

    if not accounts:
        click.echo("ℹ️  No accounts configured.")
        return

    click.echo("📘 Configured GitHub accounts:")
    for acc in accounts:
        name = acc.get("name", "<no-name>")
        username = acc.get("username", "<no-username>")
        marker = "👉" if name == active else "  "
        click.echo(f"{marker} {name} ({username})")
