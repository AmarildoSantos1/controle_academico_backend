import json
import secrets
import time
import os
from typing import Optional

ADMIN_FILE = os.path.join("data", "admin.json")
TOKENS_FILE = os.path.join("data", "tokens.json")

# -----------------------------
# Utilitários básicos
# -----------------------------
def _load_json(path: str):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# Admin
# -----------------------------
def ensure_admin():
    """Cria admin padrão caso não exista."""
    if not os.path.exists(ADMIN_FILE):
        os.makedirs(os.path.dirname(ADMIN_FILE), exist_ok=True)
        with open(ADMIN_FILE, "w", encoding="utf-8") as f:
            json.dump({"username": "admin", "password": "1234"}, f)
        print("✅ Admin criado: usuário=admin senha=1234")

def verify_user(username: str, password: str) -> bool:
    data = _load_json(ADMIN_FILE)
    return data.get("username") == username and data.get("password") == password

def change_password(old_pwd: str, new_pwd: str):
    data = _load_json(ADMIN_FILE)
    if data.get("password") != old_pwd:
        raise ValueError("Senha antiga incorreta.")
    data["password"] = new_pwd
    _save_json(ADMIN_FILE, data)

# -----------------------------
# Tokens
# -----------------------------
TOKEN_EXPIRATION = 8 * 60 * 60  # 8 horas

def issue_token() -> str:
    token = secrets.token_hex(16)
    tokens = _load_json(TOKENS_FILE)
    tokens[token] = int(time.time()) + TOKEN_EXPIRATION
    _save_json(TOKENS_FILE, tokens)
    return token

def validate_token(token: str) -> bool:
    tokens = _load_json(TOKENS_FILE)
    expiry = tokens.get(token)
    if not expiry:
        return False
    if expiry < int(time.time()):
        del tokens[token]
        _save_json(TOKENS_FILE, tokens)
        return False
    return True

def revoke_token(token: str):
    tokens = _load_json(TOKENS_FILE)
    if token in tokens:
        del tokens[token]
        _save_json(TOKENS_FILE, tokens)
