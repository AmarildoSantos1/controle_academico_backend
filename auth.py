import json
import secrets
import time
import os
import hashlib
from typing import Optional

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
ADMIN_FILE = os.path.join(DATA_DIR, "admin.json")
TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")

os.makedirs(DATA_DIR, exist_ok=True)

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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -----------------------------
# Criptografia de senha
# -----------------------------
def _hash_password(password: str, salt: str) -> str:
    """Gera hash PBKDF2-HMAC-SHA256 em hex."""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        100_000,
    )
    return dk.hex()


def _verify_password(password: str, salt: str, password_hash: str) -> bool:
    return _hash_password(password, salt) == password_hash


def _migrate_plain_password(data: dict) -> dict:
    """
    Se ainda existir 'password' em texto puro, converte para
    'salt' + 'password_hash' automaticamente.
    """
    if "password_hash" in data and "salt" in data:
        return data

    if "password" in data:
        plain = data["password"]
        salt = secrets.token_hex(16)
        password_hash = _hash_password(plain, salt)
        data.pop("password", None)
        data["salt"] = salt
        data["password_hash"] = password_hash
    return data


# -----------------------------
# Admin
# -----------------------------
def ensure_admin():
    """
    Garante que existe um admin.
    Se não houver, cria admin/admin com senha 1234 (já hasheada).
    """
    data = _load_json(ADMIN_FILE)
    if not data:
        salt = secrets.token_hex(16)
        default_pwd = "1234"
        data = {
            "username": "admin",
            "salt": salt,
            "password_hash": _hash_password(default_pwd, salt),
        }
        _save_json(ADMIN_FILE, data)
        print("✅ Admin padrão criado: usuário=admin senha=1234 (armazenada com hash)")
        return

    # migra formato antigo (se tiver)
    data = _migrate_plain_password(data)
    _save_json(ADMIN_FILE, data)


def verify_user(username: str, password: str) -> bool:
    data = _load_json(ADMIN_FILE)
    if not data:
        return False

    data = _migrate_plain_password(data)
    _save_json(ADMIN_FILE, data)

    if data.get("username") != username:
        return False

    salt = data.get("salt")
    password_hash = data.get("password_hash")
    if not salt or not password_hash:
        return False

    return _verify_password(password, salt, password_hash)


def change_password(old_password: str, new_password: str):
    data = _load_json(ADMIN_FILE)
    if not data:
        raise ValueError("Admin não configurado.")

    data = _migrate_plain_password(data)

    salt = data.get("salt")
    password_hash = data.get("password_hash")
    if not salt or not password_hash or not _verify_password(old_password, salt, password_hash):
        raise ValueError("Senha antiga incorreta.")

    new_salt = secrets.token_hex(16)
    data["salt"] = new_salt
    data["password_hash"] = _hash_password(new_password, new_salt)
    _save_json(ADMIN_FILE, data)


# -----------------------------
# Tokens (login)
# -----------------------------
TOKEN_EXPIRATION = 8 * 60 * 60  # 8 horas


def issue_token() -> str:
    """Gera e salva um token com data de expiração."""
    tokens = _load_json(TOKENS_FILE)
    token = secrets.token_hex(16)
    tokens[token] = int(time.time()) + TOKEN_EXPIRATION
    _save_json(TOKENS_FILE, tokens)
    return token


def validate_token(token: str) -> bool:
    tokens = _load_json(TOKENS_FILE)
    expiry = tokens.get(token)
    if not expiry:
        return False
    if expiry < int(time.time()):
        # expirou -> remove
        del tokens[token]
        _save_json(TOKENS_FILE, tokens)
        return False
    return True


def revoke_token(token: str):
    tokens = _load_json(TOKENS_FILE)
    if token in tokens:
        del tokens[token]
        _save_json(TOKENS_FILE, tokens)
