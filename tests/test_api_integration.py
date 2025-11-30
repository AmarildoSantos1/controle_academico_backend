import os
import sys
import json
from fastapi.testclient import TestClient

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from app import app  # importa a API FastAPI

client = TestClient(app)

DATA_DIR = os.path.join(ROOT_DIR, "data")
ALUNOS_FILE = os.path.join(DATA_DIR, "alunos.json")


def _cleanup_test_student():
    """
    Remove apenas o aluno de teste da base de dados (alunos.json),
    sem mexer nos demais alunos cadastrados.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(ALUNOS_FILE):
        return

    try:
        with open(ALUNOS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = []

    if not isinstance(data, list):
        data = []

    # Mantém todos os alunos, exceto o aluno de teste
    new_data = []
    for a in data:
        tipo = a.get("tipo_id")
        ident = a.get("identificador")
        # aluno usado no teste integrado
        if tipo == "MATRICULA" and ident == "2025A0001":
            continue
        new_data.append(a)

    with open(ALUNOS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)


def _login_admin():
    resp = client.post(
        "/auth/login",
        json={"username": "admin", "password": "1234"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    return data["token"]


def test_fluxo_completo_aluno_disciplina_notas_e_logs():
    # Remove apenas o aluno de teste, preservando alunos reais da base
    _cleanup_test_student()

    token = _login_admin()
    headers = {"Authorization": f"Bearer {token}"}

    # 1) Criar aluno de teste
    resp = client.post(
        "/students",
        headers=headers,
        json={
            "nome": "João Teste",
            "tipo_id": "MATRICULA",
            "identificador": "2025A0001",
            "data_cadastro": "2025-11-11",
            "ativo": True,
        },
    )
    assert resp.status_code == 200
    aluno = resp.json()
    aid = aluno["id"]

    # 2) Adicionar disciplina
    resp = client.post(
        f"/students/{aid}/courses",
        headers=headers,
        json={
            "nome": "Segurança da Informação",
            "data_cadastro": "2025-11-11",
        },
    )
    assert resp.status_code == 200
    disc = resp.json()
    did = disc["id"]

    # 3) Lançar notas (E1, E2, E3)
    for estagio, nota in [("E1", 8), ("E2", 7), ("E3", 9)]:
        resp = client.patch(
            f"/students/{aid}/courses/{did}/grade",
            headers=headers,
            json={"estagio": estagio, "nota": nota},
        )
        assert resp.status_code == 200
        disc = resp.json()

    assert disc["media"] >= 7
    assert disc["status"] == "APROVADO"

    # 4) Verificar relatório CSV do aluno
    resp = client.get(f"/students/{aid}/report.csv", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")

    # 5) Verificar logs (devem conter 'mensagem' decifrada)
    resp = client.get("/logs", headers=headers)
    assert resp.status_code == 200
    logs = resp.json()
    assert isinstance(logs, list)
    if logs:
        assert "mensagem" in logs[0]
