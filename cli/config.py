import json
import os
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any
from typing import Optional

import keyring

KEYRING_SERVICE = "ghmulti"
LINKED_GIT_CONFIG_KEY = "ghmulti.linkedaccount"
CONFIG_PATH = Path.home() / ".ghmulti.json"
PROJECT_CONFIG_FILE = ".ghmulti"
DEFAULT_CONFIG = {"accounts": [], "active": None}


def _as_path(value: str | Path) -> Path:
    return value if isinstance(value, Path) else Path(value)


def _project_config_path(repo_path: str | Path = ".") -> Path:
    project_config = _as_path(PROJECT_CONFIG_FILE)
    if project_config.is_absolute():
        return project_config
    return _as_path(repo_path) / project_config


def _normalize_config(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return deepcopy(DEFAULT_CONFIG)

    accounts = raw.get("accounts", [])
    normalized_accounts = []
    if isinstance(accounts, list):
        for account in accounts:
            if not isinstance(account, dict):
                continue
            name = account.get("name")
            username = account.get("username")
            if not isinstance(name, str) or not name.strip():
                continue
            if not isinstance(username, str) or not username.strip():
                continue
            normalized_account = {
                "name": name.strip(),
                "username": username.strip()
            }
            gpg_key_id = account.get("gpg_key_id")
            if isinstance(gpg_key_id, str) and gpg_key_id.strip():
                normalized_account["gpg_key_id"] = gpg_key_id.strip()

            ssh_key_path = account.get("ssh_key_path")
            if isinstance(ssh_key_path, str) and ssh_key_path.strip():
                normalized_account["ssh_key_path"] = ssh_key_path.strip()

            normalized_accounts.append(normalized_account)

    active = raw.get("active")
    if not isinstance(active, str) or not active.strip():
        active = None
    else:
        active = active.strip()

    if active and active not in {account["name"] for account in normalized_accounts}:
        active = None

    return {"accounts": normalized_accounts, "active": active}


def load_config() -> dict[str, Any]:
    config_path = _as_path(CONFIG_PATH)
    if not config_path.exists():
        return deepcopy(DEFAULT_CONFIG)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return _normalize_config(raw)
    except (json.JSONDecodeError, OSError):
        return deepcopy(DEFAULT_CONFIG)


def save_config(data: dict[str, Any]) -> None:
    config_path = _as_path(CONFIG_PATH)
    normalized = _normalize_config(data)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2)


def get_accounts() -> list[dict[str, Any]]:
    return load_config().get("accounts", [])


def get_account_by_name(account_name: str) -> Optional[dict[str, Any]]:
    for account in get_accounts():
        if account.get("name") == account_name:
            return account
    return None


def set_active_account(account_name: Optional[str]) -> None:
    data = load_config()
    if account_name is not None and not get_account_by_name(account_name):
        raise ValueError(f"Account '{account_name}' does not exist.")
    data["active"] = account_name
    save_config(data)


def get_active_account_from_global_config() -> Optional[dict[str, Any]]:
    data = load_config()
    active_name = data.get("active")
    if not active_name:
        return None
    return next((account for account in data.get("accounts", []) if account["name"] == active_name), None)


def get_git_config_value(scope: str, key: str, cwd: str | Path | None = None) -> Optional[str]:
    try:
        output = subprocess.check_output(
            ["git", "config", scope, key],
            stderr=subprocess.PIPE,
            cwd=str(cwd) if cwd else None,
            text=True
        )
        if isinstance(output, subprocess.CalledProcessError):
            return None
        if isinstance(output, bytes):
            output = output.decode()
        output = str(output).strip()
        return output or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def set_git_config_value(scope: str, key: str, value: str, cwd: str | Path | None = None) -> None:
    subprocess.run(
        ["git", "config", scope, key, value],
        check=True,
        cwd=str(cwd) if cwd else None
    )


def unset_git_config_value(scope: str, key: str, cwd: str | Path | None = None) -> None:
    subprocess.run(
        ["git", "config", scope, "--unset-all", key],
        check=False,
        cwd=str(cwd) if cwd else None
    )


def get_linked_account(repo_path: str | Path = ".") -> Optional[str]:
    project_path = _project_config_path(repo_path)
    if project_path.exists():
        try:
            with open(project_path, "r", encoding="utf-8") as f:
                project_config = json.load(f)
            account = project_config.get("account")
            if isinstance(account, str) and account.strip():
                return account.strip()
            return None
        except (json.JSONDecodeError, OSError):
            return None

    return None


def set_linked_account(account_name: str, repo_path: str | Path = ".") -> None:
    project_path = _project_config_path(repo_path)
    with open(project_path, "w", encoding="utf-8") as f:
        json.dump({"account": account_name}, f, indent=2)

    # Keep local git config in sync for compatibility with older tooling.
    set_git_config_value("--local", LINKED_GIT_CONFIG_KEY, account_name, cwd=repo_path)


def clear_linked_account(repo_path: str | Path = ".") -> None:
    project_path = _project_config_path(repo_path)
    if project_path.exists():
        project_path.unlink()

    unset_git_config_value("--local", LINKED_GIT_CONFIG_KEY, cwd=repo_path)


def get_active_account(repo_path: str | Path = ".") -> Optional[dict[str, Any]]:
    data = load_config()
    linked_account_name = get_linked_account(repo_path=repo_path)
    if linked_account_name:
        linked_account = next(
            (account for account in data.get("accounts", []) if account["name"] == linked_account_name),
            None
        )
        if linked_account:
            return linked_account

    return get_active_account_from_global_config()


def get_token(username: str) -> Optional[str]:
    return keyring.get_password(KEYRING_SERVICE, username)


def set_token(username: str, token: str) -> None:
    keyring.set_password(KEYRING_SERVICE, username, token)


def delete_token(username: str) -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, username)
    except keyring.errors.PasswordDeleteError:
        return
