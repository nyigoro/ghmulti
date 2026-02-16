import os
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from typing import Optional


def is_git_repository(cwd: str | Path = ".") -> bool:
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(cwd),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def list_remote_names(cwd: str | Path = ".") -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "remote"],
            cwd=str(cwd),
            stderr=subprocess.PIPE,
            text=True
        )
        if isinstance(output, bytes):
            output = output.decode()
        output = output.strip()
        return [line.strip() for line in output.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def choose_remote(linked_account_name: Optional[str], requested_remote: Optional[str], cwd: str | Path = ".") -> str:
    if requested_remote:
        return requested_remote

    if linked_account_name:
        linked_remote = f"origin-{linked_account_name}"
        if linked_remote in list_remote_names(cwd=cwd):
            return linked_remote

    return "origin"


def get_git_config_value(scope: str, key: str, cwd: str | Path = ".") -> Optional[str]:
    try:
        output = subprocess.check_output(
            ["git", "config", scope, key],
            cwd=str(cwd),
            stderr=subprocess.PIPE,
            text=True
        ).strip()
        return output or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


@contextmanager
def git_auth_env(token: Optional[str], username: Optional[str] = None) -> Iterator[dict[str, str]]:
    env = os.environ.copy()
    if not token:
        yield env
        return

    script_path = _create_askpass_script()
    env["GIT_ASKPASS"] = script_path
    env["GHMULTI_GIT_PASSWORD"] = token
    env["GIT_TERMINAL_PROMPT"] = "0"

    # Kept for backward compatibility with prior behavior/tests.
    if username:
        env["GIT_USERNAME"] = username
    env["GIT_PASSWORD"] = token

    try:
        yield env
    finally:
        try:
            os.remove(script_path)
        except OSError:
            pass


def _create_askpass_script() -> str:
    if os.name == "nt":
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cmd", delete=False, encoding="utf-8") as f:
            f.write("@echo %GHMULTI_GIT_PASSWORD%\n")
            return f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False, encoding="utf-8") as f:
        f.write("#!/usr/bin/env sh\n")
        f.write("printf '%s\\n' \"$GHMULTI_GIT_PASSWORD\"\n")
        path = f.name
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    return path
