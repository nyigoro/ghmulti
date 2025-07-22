import os
import sys
import click
import subprocess
from cli.config import get_active_account, get_token, load_config

@click.command(name="clone")
@click.argument("repo_url")
@click.option("--account", "account_name", default=None, help="Account name to link after cloning.")
def clone_repo(repo_url, account_name):
    """Clone a GitHub repository and optionally link it to a ghmulti account."""
    click.echo(f"Starting clone of {repo_url}...")

    # Determine which account to use for cloning if specified
    account_to_use = None
    if account_name:
        config = load_config()
        accounts = config.get("accounts", [])
        account_to_use = next((a for a in accounts if a["name"] == account_name), None)
        if not account_to_use:
            click.echo(f"❌ Account '{account_name}' not found in ghmulti config. Cloning without linking.")
            account_name = None # Reset to not link

    # Prepare environment for cloning with token if available
    env = os.environ.copy()
    if account_to_use and get_token(account_to_use["username"]):
        token = get_token(account_to_use["username"])
        env["GIT_ASKPASS"] = "echo"
        env["GIT_USERNAME"] = account_to_use["username"]
        env["GIT_PASSWORD"] = token
        click.echo(f"ℹ️  Attempting to clone using token for {account_to_use["username"]}")

    try:
        # Extract repo name from URL to determine clone directory
        repo_dir = repo_url.split('/')[-1]
        if repo_dir.endswith('.git'):
            repo_dir = repo_dir[:-4]

        subprocess.run(["git", "clone", repo_url], check=True, env=env)
        click.echo(f"✅ Successfully cloned {repo_url} into {repo_dir}/")

        # Change directory into the cloned repo
        os.chdir(repo_dir)

        if account_name:
            # Link the account automatically
            click.echo(f"🔗 Linking repository to account '{account_name}'...")
            subprocess.run(["ghmulti", "link", account_name], check=True)
        else:
            click.echo("ℹ️  No account specified for linking. You can link one manually:")
            click.echo("    `ghmulti link <account_name>`")
            # Optionally, prompt interactively if no account was specified
            if click.confirm("Do you want to link an account to this repository now?"):
                subprocess.run(["ghmulti", "use"], check=True) # Use the interactive 'use' command
                # After 'use', we need to get the active account and then link it
                # This is a bit indirect, but leverages existing interactive 'use'
                # A direct interactive 'link' would be better, but 'use' is already interactive.
                # For now, we'll assume 'use' sets the global active, and then we link that.
                active_acc = get_active_account()
                if active_acc:
                    click.echo(f"🔗 Linking repository to globally active account '{active_acc['name']}'...")
                    subprocess.run(["ghmulti", "link", active_acc['name']], check=True)

    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Git clone failed: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)
