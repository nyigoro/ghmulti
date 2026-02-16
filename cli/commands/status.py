import json
from typing import Any
from typing import Optional

import click

from cli.config import LINKED_GIT_CONFIG_KEY
from cli.config import get_active_account
from cli.config import get_active_account_from_global_config
from cli.config import get_git_config_value
from cli.config import get_linked_account
from cli.config import get_token
from cli.github_auth import validate_github_token


def _collect_git_identity(scope: str, repo_path: str = ".") -> dict[str, Optional[str]]:
    return {
        "user_name": get_git_config_value(scope, "user.name", cwd=repo_path),
        "user_email": get_git_config_value(scope, "user.email", cwd=repo_path),
        "user_signingkey": get_git_config_value(scope, "user.signingkey", cwd=repo_path),
        "core_ssh_command": get_git_config_value(scope, "core.sshCommand", cwd=repo_path),
    }


def build_status_payload(repo_path: str = ".", skip_token_check: bool = False) -> dict[str, Any]:
    linked_account_name = get_linked_account(repo_path=repo_path)
    linked_git_config = get_git_config_value("--local", LINKED_GIT_CONFIG_KEY, cwd=repo_path)
    global_active_account = get_active_account_from_global_config()
    effective_active_account = get_active_account(repo_path=repo_path)
    local_git = _collect_git_identity("--local", repo_path=repo_path)
    global_git = _collect_git_identity("--global", repo_path=repo_path)

    warnings: list[str] = []
    token_details = {
        "present": False,
        "valid": None,
        "message": "No active account to validate token for.",
        "status_code": None
    }

    if linked_account_name and linked_git_config and linked_account_name != linked_git_config:
        warnings.append(
            f"Linked account mismatch between .ghmulti ('{linked_account_name}') and git config ('{linked_git_config}')."
        )

    if effective_active_account:
        token = get_token(effective_active_account["username"])
        if token:
            token_details["present"] = True
            if skip_token_check:
                token_details["message"] = "Token check skipped."
            else:
                validation = validate_github_token(token)
                token_details["valid"] = validation.valid
                token_details["message"] = validation.message
                token_details["status_code"] = validation.status_code
        else:
            token_details["message"] = "Token not found in keyring for effective account."

    effective_username = effective_active_account["username"] if effective_active_account else None
    local_username = local_git.get("user_name")
    global_username = global_git.get("user_name")
    if effective_username:
        if local_username and local_username != effective_username:
            warnings.append(
                f"Local git user.name '{local_username}' does not match effective account username '{effective_username}'."
            )
        elif not local_username and global_username and global_username != effective_username:
            warnings.append(
                f"Global git user.name '{global_username}' does not match effective account username '{effective_username}'."
            )
        elif not local_username and not global_username:
            warnings.append("No git user.name configured.")

    return {
        "linked_account": linked_account_name,
        "linked_account_from_git_config": linked_git_config,
        "global_active_account": global_active_account,
        "effective_active_account": effective_active_account,
        "local_git": local_git,
        "global_git": global_git,
        "token": token_details,
        "warnings": warnings,
    }


def _echo_identity(label: str, identity: dict[str, Optional[str]]) -> None:
    if any(identity.values()):
        click.echo(
            f"✒️  User: {identity['user_name'] or 'Not set'} <{identity['user_email'] or 'Not set'}>"
        )
        if identity["user_signingkey"]:
            click.echo(f"   Signing Key: {identity['user_signingkey']}")
        if identity["core_ssh_command"]:
            click.echo(f"   SSH Command: {identity['core_ssh_command']}")
    else:
        click.echo("    Not set.")


@click.command(name="status")
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
@click.option("--skip-token-check", is_flag=True, help="Skip online GitHub token validation.")
def status(json_output: bool, skip_token_check: bool):
    """Show the current ghmulti status and active account."""
    payload = build_status_payload(skip_token_check=skip_token_check)

    if json_output:
        click.echo(json.dumps(payload, indent=2))
        return

    click.echo("🔎 Checking ghmulti status...")

    linked_account_name = payload["linked_account"]
    if linked_account_name:
        click.echo(f"🔗 Repository linked to: '{linked_account_name}' (via .ghmulti)")
    else:
        click.echo("ℹ️  Repository not linked to any account.")

    global_active_account = payload["global_active_account"]
    if global_active_account:
        click.echo(
            f"👤 Global active account: '{global_active_account['name']}' ({global_active_account['username']})"
        )
    else:
        click.echo("❌ No global active account configured. Run `ghmulti use`.")

    effective_active_account = payload["effective_active_account"]
    if effective_active_account:
        click.echo(
            f"✨ Effective active account for this repository: '{effective_active_account['name']}' "
            f"({effective_active_account['username']})"
        )
    else:
        click.echo("❌ No effective active account found for this repository.")

    click.echo("\n--- Local Git Config (for this repository) ---")
    _echo_identity("Local", payload["local_git"])

    click.echo("\n--- Global Git Config (default for all repositories) ---")
    _echo_identity("Global", payload["global_git"])

    click.echo("\n--- Token Status ---")
    token = payload["token"]
    if token["present"]:
        prefix = "✅" if token["valid"] is True else ("❌" if token["valid"] is False else "ℹ️ ")
        click.echo(f"{prefix} {token['message']}")
    else:
        click.echo(f"ℹ️  {token['message']}")

    if payload["warnings"]:
        click.echo("\n--- Warnings ---")
        for warning in payload["warnings"]:
            click.echo(f"⚠️  {warning}")
