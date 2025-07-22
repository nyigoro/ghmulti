# cli/commands/link.py
import os
import json
import click
import subprocess
import re
from cli.config import load_config

PROJECT_CONFIG_FILE = ".ghmulti"

@click.command(name="link")
@click.argument("account_name")
def link_account(account_name):
    """Link a GitHub account to the current repository."""
    config = load_config()
    accounts = config.get("accounts", [])
    
    target_account = next((acc for acc in accounts if acc["name"] == account_name), None)
    if not target_account:
        click.echo(f"❌ Account '{account_name}' not found in your ghmulti config.")
        click.echo("Run `ghmulti list` to see available accounts.")
        return

    if not os.path.exists(".git"):
        click.echo("❌ This does not appear to be a git repository.")
        return

    # Create the .ghmulti project file
    project_config = {"account": account_name}
    with open(PROJECT_CONFIG_FILE, "w") as f:
        json.dump(project_config, f, indent=2)
    
    click.echo(f"✅ Successfully linked account '{account_name}' to this repository.")

    # Smart remote management
    check_and_manage_remotes(target_account)

def check_and_manage_remotes(account):
    try:
        remotes_output = subprocess.check_output(["git", "remote", "-v"]).decode()
    except subprocess.CalledProcessError:
        click.echo("    Could not check git remotes.")
        return

    username = account["username"]
    # Check if a remote URL already contains the username
    if username.lower() in remotes_output.lower():
        click.echo(f"    Found existing remote that may be associated with '{username}'.")
        return

    # If no remote seems to match, offer to add one.
    click.echo(f"    No remote found for user '{username}'.")
    if click.confirm(f"    Do you want to add a remote for '{username}'?"):
        try:
            origin_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode().strip()

            # Determine if it's an SSH or HTTPS URL
            is_ssh = origin_url.startswith("git@")
            
            # Extract the 'owner/repo.git' part
            match = re.search(r'(?:github\.com[:/])([^/]+/[^/]+(?:\.git)?)', origin_url)
            if not match:
                raise ValueError("Could not parse origin URL format.")
            
            owner_repo_part = match.group(1) # e.g., 'original-owner/repo.git'

            # Replace the owner part with the new username
            repo_only_name = owner_repo_part.split('/', 1)[1] # e.g., 'repo.git'

            if is_ssh:
                new_remote_url = f"git@github.com:{username}/{repo_only_name}"
            else: # HTTPS
                new_remote_url = f"https://github.com/{username}/{repo_only_name}"
            
            remote_name = f"origin-{username}" # A safe default remote name

            click.echo(f"    Adding remote '{remote_name}' with URL: {new_remote_url}")
            subprocess.run(["git", "remote", "add", remote_name, new_remote_url], check=True)
            click.echo("    ✅ Remote added.")
        except (subprocess.CalledProcessError, ValueError, IndexError) as e:
            click.echo(f"    ❌ Could not automatically determine remote URL. Please add it manually. Error: {e}")
