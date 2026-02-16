import click
from cli.config import load_config
from cli.config import save_config
from cli.config import set_token


@click.command(name="add")
@click.option("--name", default=None, help="Local account alias (e.g., personal, work).")
@click.option("--username", default=None, help="GitHub username for this account.")
@click.option("--token", default=None, help="GitHub Personal Access Token.")
@click.option("--gpg-key-id", default=None, help="GPG signing key ID to set when using this account.")
@click.option("--ssh-key-path", default=None, help="SSH private key path for this account.")
@click.option("--set-active", is_flag=True, help="Set the account as the global active account.")
def add_account(name, username, token, gpg_key_id, ssh_key_path, set_active):
    """Add a new GitHub account."""
    fully_interactive = all(
        value is None for value in [name, username, token, gpg_key_id, ssh_key_path]
    )

    name = (name or click.prompt("Account name")).strip()
    username = (username or click.prompt("GitHub username")).strip()

    if token is None:
        token = click.prompt(
            "Personal access token (optional, leave blank for SSH)",
            default="",
            show_default=False,
            hide_input=True
        )
    token = token.strip()

    if gpg_key_id is None and fully_interactive:
        gpg_key_id = click.prompt("GPG Signing Key ID (optional)", default="", show_default=False)
    gpg_key_id = (gpg_key_id or "").strip()

    if ssh_key_path is None and fully_interactive:
        ssh_key_path = click.prompt(
            "SSH Key Path (e.g., ~/.ssh/id_rsa_github_personal, optional)",
            default="",
            show_default=False
        )
    ssh_key_path = (ssh_key_path or "").strip()

    if not name or not username:
        raise click.ClickException("Account name and GitHub username are required.")

    if not token and not ssh_key_path:
        raise click.ClickException("Either a Personal Access Token or an SSH Key Path is required.")

    config = load_config()

    # Check if account with same name exists
    if any(a["name"] == name for a in config["accounts"]):
        click.echo(f"❌ Account '{name}' already exists.")
        return

    new_account = {
        "name": name,
        "username": username,
    }
    if gpg_key_id:
        new_account["gpg_key_id"] = gpg_key_id
    if ssh_key_path:
        new_account["ssh_key_path"] = ssh_key_path

    config["accounts"].append(new_account)

    if token:
        set_token(username, token)

    if set_active or not config.get("active"):
        config["active"] = name

    save_config(config)

    click.echo(f"✅ Added account '{name}' and saved.")
    if token:
        click.echo("🔐 Token saved to keyring.")
    if config.get("active") == name:
        click.echo(f"✨ Active account is now '{name}'.")
