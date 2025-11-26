import requests

API_URL = "http://127.0.0.1:8000"

token = None


def auth_headers():
    global token
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def fazer_login():
    global token
    print("\n=== LOGIN ===")
    username = input("Usuário: ").strip()
    password = input("Senha: ").strip()

    resp = requests.post(f"{API_URL}/auth/login", json={
        "username": username,
        "password": password,
    })

    if resp.status_code == 200:
        token = resp.json()["token"]
        print("✅ Login OK.")
    else:
        print("❌ Erro no login:", resp.status_code, resp.text)


def listar_alunos():
    resp = requests.get(f"{API_URL}/students", headers=auth_headers())
    if resp.status_code != 200:
        print("❌ Erro ao listar alunos:", resp.status_code, resp.text)
        return
    alunos = resp.json()
    if not alunos:
        print("Nenhum aluno cadastrado.")
        return
    print("\n=== ALUNOS ===")
    for a in alunos:
        print(f"ID: {a['id']} | Nome: {a['nome']} | Ativo: {a['ativo']}")
        print(f"  Tipo/ID: {a['tipo_id']} {a['identificador']}")
        print(f"  Disciplinas: {len(a['disciplinas'])}")
        print("-" * 40)


def criar_aluno():
    print("\n=== NOVO ALUNO ===")
    nome = input("Nome: ").strip()
    tipo_id = input("Tipo identificador (MATRICULA/CPF): ").strip().upper()
    identificador = input("Identificador: ").strip()

    resp = requests.post(
        f"{API_URL}/students",
        headers=auth_headers(),
        json={
            "nome": nome,
            "tipo_id": tipo_id,
            "identificador": identificador,
            "data_cadastro": None,
            "ativo": True,
        }
    )
    if resp.status_code == 200:
        print("✅ Aluno criado:", resp.json()["id"])
    else:
        print("❌ Erro ao criar aluno:", resp.status_code, resp.text)


def adicionar_disciplina():
    print("\n=== ADICIONAR DISCIPLINA ===")
    aid = input("ID do aluno: ").strip()
    nome = input("Nome da disciplina: ").strip()

    resp = requests.post(
        f"{API_URL}/students/{aid}/courses",
        headers=auth_headers(),
        json={"nome": nome, "data_cadastro": None}
    )
    if resp.status_code == 200:
        d = resp.json()
        print("✅ Disciplina criada:", d["id"], "-", d["nome"])
    else:
        print("❌ Erro:", resp.status_code, resp.text)


def lancar_nota():
    print("\n=== LANÇAR NOTA ===")
    aid = input("ID do aluno: ").strip()
    did = input("ID da disciplina: ").strip()
    estagio = input("Estágio (E1/E2/E3): ").strip().upper()
    nota = float(input("Nota (0..10): ").strip())

    resp = requests.patch(
        f"{API_URL}/students/{aid}/courses/{did}/grade",
        headers=auth_headers(),
        json={"estagio": estagio, "nota": nota}
    )
    if resp.status_code == 200:
        print("✅ Nota lançada.")
    else:
        print("❌ Erro ao lançar nota:", resp.status_code, resp.text)


def menu():
    while True:
        print("\n=== CONTROLE ACADÊMICO (CLI) ===")
        print("1) Login")
        print("2) Listar alunos")
        print("3) Criar aluno")
        print("4) Adicionar disciplina a aluno")
        print("5) Lançar nota em disciplina")
        print("0) Sair")
        op = input("Opção: ").strip()

        if op == "1":
            fazer_login()
        elif op == "2":
            listar_alunos()
        elif op == "3":
            criar_aluno()
        elif op == "4":
            adicionar_disciplina()
        elif op == "5":
            lancar_nota()
        elif op == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()
