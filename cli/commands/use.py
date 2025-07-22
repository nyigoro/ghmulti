import os
import sys
import click
import subprocess
import inquirer
from cli.config import load_config, save_config, get_token

def switch_account_logic(account_name):
    config = load_config()

    accounts = config.get("accounts", [])
    match = next((a for a in accounts if a["name"] == account_name), None)

    if not match:
        print(f"❌ No account named '{account_name}' found.")
        sys.exit(1)

    config["active"] = account_name
    save_config(config)
    
    token = get_token(match["username"])
    
    # Configure git user
    subprocess.run(["git", "config", "--global", "user.name", match["username"]], check=True)
    subprocess.run(["git", "config", "--global", "user.email", f'{match["username"]}@users.noreply.github.com'], check=True)

    # Configure git credential helper to use the token
    # This is a simplified approach. For more robust solutions, especially on multi-user systems,
    # consider more advanced credential helper configurations.
    credential_helper_command = f"store --file={os.path.expanduser('~/.git-credentials')}"
    subprocess.run(["git", "config", "--global", "credential.helper", credential_helper_command], check=True)
    
    # Write the token to the credential file
    # Note: This will overwrite the file with the current user's token.
    with open(os.path.expanduser("~/.git-credentials"), "w") as f:
        f.write(f"https://{match['username']}:{token}@github.com")

    print(f"✅ Switched active account to: {account_name}")

@click.command(name="use")
@click.argument("account_name", required=False)
def use_account(account_name):
    """
    Switch the active GitHub account.
    
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
                message="Which account do you want to use?",
                choices=account_choices,
                carousel=True,
            ),
        ]
        
        answers = inquirer.prompt(questions)
        
        if answers and "account" in answers:
            switch_account_logic(answers["account"])
