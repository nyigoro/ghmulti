import click
import subprocess
import json
import os
import keyring
import re

# --- Helper functions (re-introduced for self-containment) ---

CONFIG_FILE = os.path.expanduser("~/.ghmulti.json")

def get_config():
    """Loads the ghmulti configuration from the user's home directory."""
    if not os.path.exists(CONFIG_FILE):
        return {"accounts": [], "active": None}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        click.echo(f"Warning: Could not read or parse config file at {CONFIG_FILE}. It might be corrupted. Recreating.", err=True)
        return {"accounts": [], "active": None}
    except Exception as e:
        click.echo(f"Error reading config file: {e}", err=True)
        return {"accounts": [], "active": None}


def save_config(config):
    """Saves the ghmulti configuration to the user's home directory."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        click.echo(f"Error saving config file: {e}", err=True)


def get_account_by_name(account_name):
    """Retrieves an account by its name."""
    config = get_config()
    for account in config.get("accounts", []):
        if account["name"] == account_name:
            return account
    return None

def get_active_account_from_global_config():
    """
    Determines the global active account based on the .ghmulti.json config.
    """
    config = get_config()
    active_account_name = config.get("active")
    if active_account_name:
        return get_account_by_name(active_account_name)
    return None

def get_active_account():
    """
    Determines the effective active account for the current repository.
    Prioritizes local linked account, then global active account.
    """
    # Check for locally linked account
    linked_account_name = get_git_config_value("--local", "ghmulti.linkedaccount")
    if linked_account_name:
        linked_account = get_account_by_name(linked_account_name)
        if linked_account:
            return linked_account
        else:
            click.echo(f"Warning: Linked account '{linked_account_name}' not found in ghmulti config. Falling back to global active account.", err=True)

    # Fallback to global active account
    return get_active_account_from_global_config()

def get_linked_account():
    """
    Returns the name of the account linked to the current repository, if any.
    """
    return get_git_config_value("--local", "ghmulti.linkedaccount")

def get_git_config_value(scope, key):
    """
    Safely gets a git config value for a given scope and key.
    Returns the value (stripped string) or None if not set or an error occurs.
    """
    try:
        # Use stderr=subprocess.PIPE to capture stderr and avoid printing to console
        # if the config is not set.
        value = subprocess.check_output(
            ["git", "config", scope, key],
            stderr=subprocess.PIPE
        ).decode().strip()
        return value if value else None # Return None for empty strings too
    except subprocess.CalledProcessError:
        return None # Config not set or error occurred
    except Exception as e:
        click.echo(f"Warning: Error reading git config {scope} {key}: {e}", err=True)
        return None

def validate_token(token):
    """
    Validates a GitHub token by making a simple API call.
    Returns True if valid, False otherwise.
    """
    if not token:
        return False
    try:
        # Use a simple API call that doesn't require specific scopes,
        # like fetching user info.
        subprocess.run(
            ["curl", "-s", "-H", f"Authorization: token {token}",
             "https://api.github.com/user"],
            capture_output=True,
            check=True, # Raises CalledProcessError for non-zero exit codes
            env={"GIT_TERMINAL_PROMPT": "0"}, # Prevent git from asking for credentials
            shell=False # Prefer not using shell for security and consistency
        )
        return True
    except subprocess.CalledProcessError as e:
        # Token is invalid or expired (e.g., 401 Unauthorized)
        # Check stderr or stdout for more specific error messages from curl/GitHub API
        error_output = e.stderr.decode('utf-8', errors='ignore') + e.stdout.decode('utf-8', errors='ignore')
        if "Bad credentials" in error_output or "token is invalid" in error_output.lower():
            click.echo(f"❌ Token is invalid or expired. Please update it using `ghmulti add`.", err=True)
        else:
            click.echo(f"❌ Error validating token (API call failed): {e}", err=True)
        return False
    except Exception as e:
        click.echo(f"❌ An unexpected error occurred during token validation: {e}", err=True)
        return False

# --- Main status command ---

@click.command(name="status")
def status():
    """Show the current ghmulti status and active account."""
    click.echo("🔎 Checking ghmulti status...")

    linked_account_name = get_linked_account()
    global_active_account = get_active_account_from_global_config()
    effective_active_account = get_active_account()

    if linked_account_name:
        click.echo(f"🔗 Repository linked to: '{linked_account_name}' (via .ghmulti)")
    else:
        click.echo("ℹ️  Repository not linked to any account.")

    if global_active_account:
        click.echo(f"👤 Global active account: '{global_active_account['name']}' ({global_active_account['username']})")
    else:
        click.echo("❌ No global active account configured. Run `ghmulti use`.")

    if effective_active_account:
        click.echo(f"✨ Effective active account for this repository: '{effective_active_account['name']}' ({effective_active_account['username']})")
    else:
        click.echo("❌ No effective active account found for this repository.")

    # Check local git config
    click.echo("\n--- Local Git Config (for this repository) ---")
    local_user = get_git_config_value("--local", "user.name")
    local_email = get_git_config_value("--local", "user.email")
    local_signingkey = get_git_config_value("--local", "user.signingkey")
    local_ssh_command = get_git_config_value("--local", "core.sshCommand")

    if local_user or local_email or local_signingkey or local_ssh_command:
        click.echo(f"✒️  User: {local_user or 'Not set'} <{local_email or 'Not set'}>")
        if local_signingkey:
            click.echo(f"   Signing Key: {local_signingkey}")
        if local_ssh_command:
            click.echo(f"   SSH Command: {local_ssh_command}")
    else:
        click.echo("    Not set.")

    # Check global git config
    click.echo("\n--- Global Git Config (default for all repositories) ---")
    global_user = get_git_config_value("--global", "user.name")
    global_email = get_git_config_value("--global", "user.email")
    global_signingkey = get_git_config_value("--global", "user.signingkey")
    global_ssh_command = get_git_config_value("--global", "core.sshCommand")

    if global_user or global_email or global_signingkey or global_ssh_command:
        click.echo(f"✒️  User: {global_user or 'Not set'} <{global_email or 'Not set'}>")
        if global_signingkey:
            click.echo(f"   Signing Key: {global_signingkey}")
        if global_ssh_command:
            click.echo(f"   SSH Command: {global_ssh_command}")
    else:
        click.echo("    Not set.")

    # Token Status
    click.echo("\n--- Token Status ---")
    if effective_active_account:
        token = keyring.get_password("ghmulti", effective_active_account['username'])
        if token:
            validate_token(token) # This function prints its own error/success messages
        else:
            click.echo("❌ Token not found for the active account in keychain. Run `ghmulti add` to set it.")
    else:
        click.echo("ℹ️  No effective active account to check token for.")

    # Git User Mismatch Warning
    # Check if effective account username matches local git config user.name
    # If local user.name is not set, check against global user.name
    if effective_active_account:
        effective_username = effective_active_account['username']
        
        # Prioritize local git config for mismatch check
        if local_user and local_user != effective_username:
            click.echo(f"\n⚠️  Warning: Local Git user.name '{local_user}' does not match the effective active account username '{effective_username}'.")
        elif not local_user and global_user and global_user != effective_username:
            click.echo(f"\n⚠️  Warning: Global Git user.name '{global_user}' does not match the effective active account username '{effective_username}'.")
        elif not local_user and not global_user:
            click.echo("\n⚠️  Warning: No Git user.name configured. Git commits may not be attributed correctly.")
