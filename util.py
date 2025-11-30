from typing import Optional
from datetime import datetime
import os

from cryptography.fernet import Fernet

# -----------------------------
# Datas / strings
# -----------------------------
def nonempty(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    return s or None


def ensure_date(s: str):
    """Valida formato YYYY-MM-DD. Lança ValueError se inválido."""
    datetime.strptime(s, "%Y-%m-%d")


def to_date(s: str):
    """Converte 'YYYY-MM-DD' para date."""
    return datetime.strptime(s, "%Y-%m-%d").date()


# -----------------------------
# Cifra clássica: César
# -----------------------------
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def caesar_encrypt(text: str, shift: int = 3) -> str:
    """
    Cifra clássica de César.
    Classe: técnica clássica de criptografia.
    """
    res = []
    for ch in text:
        up = ch.upper()
        if up in _ALPHABET:
            idx = _ALPHABET.index(up)
            new = _ALPHABET[(idx + shift) % len(_ALPHABET)]
            res.append(new if ch.isupper() else new.lower())
        else:
            res.append(ch)
    return "".join(res)


def caesar_decrypt(text: str, shift: int = 3) -> str:
    return caesar_encrypt(text, -shift)


# -----------------------------
# Cifra simétrica: Fernet (AES)
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
FERNET_KEY_FILE = os.path.join(DATA_DIR, "fernet.key")

os.makedirs(DATA_DIR, exist_ok=True)


def _get_fernet() -> Fernet:
    """
    Usa Fernet (criptografia simétrica baseada em AES + HMAC).
    Classe: criptografia de chave simétrica.
    """
    if not os.path.exists(FERNET_KEY_FILE):
        key = Fernet.generate_key()
        with open(FERNET_KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(FERNET_KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)


def encrypt_sensitive(plain: str) -> str:
    """Cifra um dado sensível (ex: identificador de aluno)."""
    f = _get_fernet()
    token = f.encrypt(plain.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_sensitive(token: str) -> str:
    """Decifra o dado sensível cifrado com encrypt_sensitive."""
    f = _get_fernet()
    value = f.decrypt(token.encode("utf-8"))
    return value.decode("utf-8")
