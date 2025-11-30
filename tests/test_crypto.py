import os
import sys
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from util import caesar_encrypt, caesar_decrypt, encrypt_sensitive, decrypt_sensitive
from auth import ensure_admin, verify_user, change_password


def test_caesar_encrypt_decrypt_roundtrip():
    texto = "Aluno aprovado em Segurança!"
    cifrado = caesar_encrypt(texto, shift=5)
    assert cifrado != texto
    decifrado = caesar_decrypt(cifrado, shift=5)
    assert decifrado == texto


def test_encrypt_sensitive_roundtrip():
    plain = "12345678900"
    token = encrypt_sensitive(plain)
    assert token != plain
    dec = decrypt_sensitive(token)
    assert dec == plain


def test_admin_password_hash_and_verify():
    # garante que o admin existe (hash será criado se não existir)
    ensure_admin()
    assert verify_user("admin", "1234")
    assert not verify_user("admin", "senha_errada")


def test_change_password_and_revert():
    ensure_admin()
    # troca 1234 -> nova_senha
    change_password("1234", "nova_senha")
    assert verify_user("admin", "nova_senha")
    assert not verify_user("admin", "1234")

    # volta para 1234 para não quebrar outros testes / uso
    change_password("nova_senha", "1234")
    assert verify_user("admin", "1234")
