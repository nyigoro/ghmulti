# cli/commands/add.py
from cli.config import load_config, save_config

def run():
    name = input("Account name (e.g. personal, work): ").strip()
    email = input("Git email: ").strip()
    auth_type = input("Auth type (ssh/token): ").strip().lower()

    auth = {}
    if auth_type == "ssh":
        key = input("Path to SSH key (e.g. ~/.ssh/id_rsa): ").strip()
        auth = {"type": "ssh", "keyPath": key}
    elif auth_type == "token":
        token = input("GitHub token (PAT): ").strip()
        auth = {"type": "token", "token": token}
    else:
        print("❌ Unsupported auth type.")
        return

    config = load_config()

    if any(acc["name"] == name for acc in config["accounts"]):
        print(f"❌ Account '{name}' already exists.")
        return

    config["accounts"].append({
        "name": name,
        "email": email,
        "auth": auth
    })
    save_config(config)
    print(f"✅ Added account '{name}'")
