# cli/config.py
import os
import json
import keyring
from pathlib import Path

CONFIG_PATH = Path.home() / ".ghmulti.json"

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
    for acc in data["accounts"]:
        if acc["name"] == data["active"]:
            return acc
    return None

def get_token(username):
    return keyring.get_password("ghmulti", username)
