import os
import sys
import pytest

# ---------------------------------------------------------
# Ajuste essencial:
# Garante que o Python encontre storage.py e util.py
# mesmo quando o pytest roda dentro da pasta "tests".
# ---------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from storage import Disciplina
from util import nonempty, ensure_date, to_date


# ---------------------------------------------------------
# Testes da classe Disciplina
# ---------------------------------------------------------

def test_media_incompleta_retorna_none():
    d = Disciplina(
        id="1",
        nome="Matemática",
        data_cadastro="2025-01-01",
        notas={"E1": 8.0, "E2": None, "E3": 9.0},
    )
    assert d.media() is None
    assert d.status() == "EM_CURSO"


def test_media_aprovado():
    # Média: 8.1
    d = Disciplina(
        id="1",
        nome="Matemática",
        data_cadastro="2025-01-01",
        notas={"E1": 8.0, "E2": 7.0, "E3": 9.0},
    )
    assert d.media() == pytest.approx(8.1, rel=1e-2)
    assert d.status() == "APROVADO"


def test_media_reprovado():
    # Média: 5.0 → REPROVADO
    d = Disciplina(
        id="1",
        nome="História",
        data_cadastro="2025-01-01",
        notas={"E1": 5.0, "E2": 5.0, "E3": 5.0},
    )
    assert d.media() == pytest.approx(5.0, rel=1e-2)
    assert d.status() == "REPROVADO"


# ---------------------------------------------------------
# Testes de util.py
# ---------------------------------------------------------

def test_nonempty():
    assert nonempty("  oi ") == "oi"
    assert nonempty("   ") is None
    assert nonempty(None) is None


def test_ensure_date_valida():
    # data válida, não deve lançar erro
    ensure_date("2024-10-05")


def test_ensure_date_invalida():
    # formato errado → deve levantar ValueError
    with pytest.raises(ValueError):
        ensure_date("05/10/2024")


def test_to_date():
    d = to_date("2024-10-05")
    assert d.year == 2024
    assert d.month == 10
    assert d.day == 5
