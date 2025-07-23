import os
import sys
import click
import subprocess
import inquirer
from cli.config import load_config, save_config

def switch_account_logic(account_name):
    config = load_config()

    accounts = config.get("accounts", [])
    match = next((a for a in accounts if a["name"] == account_name), None)

    if not match:
        print(f"❌ No account named '{account_name}' found.")
        sys.exit(1)

    config["active"] = account_name
    save_config(config)
    
    # Configure git user globally
    subprocess.run(["git", "config", "--global", "user.name", match["username"]], check=True)
    subprocess.run(["git", "config", "--global", "user.email", f'{match["username"]}@users.noreply.github.com'], check=True)

    # Configure GPG signing key if provided
    gpg_key_id = match.get("gpg_key_id")
    if gpg_key_id:
        subprocess.run(["git", "config", "--global", "user.signingkey", gpg_key_id], check=True)
        click.echo(f"✅ Global Git GPG signing key set to: {gpg_key_id}")
    else:
        # Unset if not provided
        subprocess.run(["git", "config", "--global", "--unset-all", "user.signingkey"], check=False)
        click.echo("ℹ️  Global Git GPG signing key unset.")

    # Configure SSH command if SSH key path is provided
    ssh_key_path = match.get("ssh_key_path")
    if ssh_key_path:
        # Use ssh-agent for better security and management
        ssh_command = f"ssh -i {os.path.expanduser(ssh_key_path)}"
        subprocess.run(["git", "config", "--global", "core.sshCommand", ssh_command], check=True)
        click.echo(f"✅ Global Git SSH command set to: {ssh_command}")
    else:
        # Unset if not provided
        subprocess.run(["git", "config", "--global", "--unset-all", "core.sshCommand"], check=False)
        click.echo("ℹ️  Global Git SSH command unset.")

    print(f"✅ Switched global active account to: {account_name}")

@click.command(name="use")
@click.argument("account_name", required=False)
def use_account(account_name):
    """
    Switch the global active GitHub account.
    
    If ACCOUNT_NAME is not provided, an interactive menu will be shown.
    """
    if account_name:
        switch_account_logic(account_name)
    else:
        config = load_config()
        accounts = config.get("accounts", [])
        if not accounts:
            click.echo("ℹ️  No accounts configured. Run `ghmulti add` to add one.")
            sys.exit(0)

        account_choices = [acc["name"] for acc in accounts]
        
        questions = [
            inquirer.List(
                "account",
                message="Which account do you want to use globally?",
                choices=account_choices,
                carousel=True,
            ),
        ]
        
        answers = inquirer.prompt(questions)
        
        if answers and "account" in answers:
            switch_account_logic(answers["account"])