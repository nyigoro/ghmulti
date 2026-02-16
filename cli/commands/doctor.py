import importlib
import json
import subprocess
import sys
from dataclasses import asdict
from dataclasses import dataclass

import click
import keyring

from cli.config import get_active_account_from_global_config
from cli.config import get_linked_account
from cli.config import load_config
from cli.git_utils import is_git_repository


@dataclass
class DoctorCheck:
    name: str
    status: str
    detail: str


def _run_check(name: str, ok: bool, detail: str) -> DoctorCheck:
    return DoctorCheck(name=name, status="ok" if ok else "error", detail=detail)


@click.command(name="doctor")
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON.")
def doctor(json_output):
    """Run environment diagnostics for ghmulti."""
    checks: list[DoctorCheck] = []

    checks.append(
        _run_check(
            "python",
            sys.version_info >= (3, 10),
            f"Python {sys.version.split()[0]} (requires >= 3.10)"
        )
    )

    for dependency in ["click", "keyring", "inquirer", "requests"]:
        try:
            importlib.import_module(dependency)
            checks.append(_run_check(f"dependency:{dependency}", True, "available"))
        except Exception as exc:  # pragma: no cover - defensive
            checks.append(_run_check(f"dependency:{dependency}", False, f"missing ({exc})"))

    try:
        git_version = subprocess.check_output(["git", "--version"], text=True).strip()
        checks.append(_run_check("git", True, git_version))
    except Exception as exc:
        checks.append(_run_check("git", False, f"not available ({exc})"))

    config = load_config()
    checks.append(_run_check("config", True, f"{len(config.get('accounts', []))} account(s) configured"))

    active = get_active_account_from_global_config()
    checks.append(
        _run_check(
            "active-account",
            active is not None,
            f"active={active['name']}" if active else "no active account"
        )
    )

    try:
        backend = keyring.get_keyring()
        checks.append(_run_check("keyring-backend", True, backend.__class__.__name__))
    except Exception as exc:
        checks.append(_run_check("keyring-backend", False, f"unavailable ({exc})"))

    if is_git_repository():
        linked = get_linked_account()
        checks.append(_run_check("repo-link", True, f"linked={linked}" if linked else "repo not linked"))
    else:
        checks.append(_run_check("repo-link", True, "not in a git repository"))

    has_errors = any(check.status == "error" for check in checks)
    payload = {
        "ok": not has_errors,
        "checks": [asdict(check) for check in checks]
    }

    if json_output:
        click.echo(json.dumps(payload, indent=2))
    else:
        click.echo("ghmulti doctor\n")
        for check in checks:
            marker = "✅" if check.status == "ok" else "❌"
            click.echo(f"{marker} {check.name}: {check.detail}")

    if has_errors:
        raise SystemExit(1)
