# cli/config.py
import os
import json
import keyring
from pathlib import Path

CONFIG_PATH = Path.home() / ".ghmulti.json"
PROJECT_CONFIG_FILE = ".ghmulti"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"accounts": [], "active": None}

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def get_active_account():
    data = load_config()
    # Check for a linked account first
    linked_account = get_linked_account()
    if linked_account:
        for acc in data["accounts"]:
            if acc["name"] == linked_account:
                return acc

    for acc in data["accounts"]:
        if acc["name"] == data["active"]:
            return acc
    return None

def get_linked_account():
    if os.path.exists(PROJECT_CONFIG_FILE):
        with open(PROJECT_CONFIG_FILE, "r") as f:
            try:
                project_config = json.load(f)
                return project_config.get("account")
            except json.JSONDecodeError:
                return None
    return None

def get_token(username):
    return keyring.get_password("ghmulti", username)
