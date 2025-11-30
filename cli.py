import requests

BASE_URL = "http://127.0.0.1:8000"
TOKEN = None


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def _auth_headers():
    global TOKEN
    if not TOKEN:
        return {}
    return {"Authorization": f"Bearer {TOKEN}"}


# ------------------------------------------------------------------------------
# AUTENTICAÇÃO
# ------------------------------------------------------------------------------
def do_login():
    global TOKEN
    print("\n=== LOGIN ===")
    username = input("Usuário [admin]: ").strip() or "admin"
    password = input("Senha [1234]: ").strip() or "1234"

    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"❌ Erro de conexão com a API: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Falha no login: {resp.status_code} {resp.text}")
        return

    data = resp.json()
    TOKEN = data.get("token")
    print("✅ Login realizado com sucesso.")


# ------------------------------------------------------------------------------
# ALUNOS
# ------------------------------------------------------------------------------
def listar_alunos():
    if not TOKEN:
        print("⚠️  Você precisa fazer login primeiro (opção 1).")
        return

    print("\n=== ALUNOS ===")
    try:
        resp = requests.get(
            f"{BASE_URL}/students",
            headers=_auth_headers(),
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"❌ Erro de conexão ao listar alunos: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Erro ao listar alunos: {resp.status_code} {resp.text}")
        return

    alunos = resp.json()
    if not alunos:
        print("Nenhum aluno cadastrado.")
        return

    for a in alunos:
        print(f"ID: {a['id']} | Nome: {a['nome']} | Ativo: {a['ativo']}")
        print(f"  Tipo/ID: {a['tipo_id']} {a['identificador']}")
        print(f"  Disciplinas: {len(a.get('disciplinas', []))}")
        print("-" * 40)


def criar_aluno():
    if not TOKEN:
        print("⚠️  Você precisa fazer login primeiro (opção 1).")
        return

    print("\n=== NOVO ALUNO ===")
    nome = input("Nome: ").strip()
    tipo_id = input("Tipo do identificador (MATRICULA/CPF) [MATRICULA]: ").strip().upper() or "MATRICULA"
    identificador = input("Identificador (matrícula ou CPF): ").strip()
    data_cadastro = input("Data de cadastro (YYYY-MM-DD) [hoje]: ").strip()
    ativo = (input("Ativo? (S/N) [S]: ").strip().upper() or "S") == "S"

    payload = {
        "nome": nome,
        "tipo_id": tipo_id,
        "identificador": identificador,
        "data_cadastro": data_cadastro or None,
        "ativo": ativo,
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/students",
            headers=_auth_headers(),
            json=payload,
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"❌ Erro de conexão ao criar aluno: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Erro ao criar aluno: {resp.status_code} {resp.text}")
        return

    a = resp.json()
    print("✅ Aluno criado com sucesso!")
    print(f"ID: {a['id']} | Nome: {a['nome']}")


# ------------------------------------------------------------------------------
# DISCIPLINAS
# ------------------------------------------------------------------------------
def adicionar_disciplina():
    if not TOKEN:
        print("⚠️  Você precisa fazer login primeiro.")
        return

    print("\n=== ADICIONAR DISCIPLINA ===")
    aid = input("ID do aluno: ").strip()
    nome = input("Nome da disciplina: ").strip()
    data_cadastro = input("Data (YYYY-MM-DD) [hoje]: ").strip()

    payload = {"nome": nome, "data_cadastro": data_cadastro or None}

    try:
        resp = requests.post(
            f"{BASE_URL}/students/{aid}/courses",
            headers=_auth_headers(),
            json=payload,
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"❌ Erro ao criar disciplina: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Erro ao criar disciplina: {resp.status_code} {resp.text}")
        return

    d = resp.json()
    print("✅ Disciplina criada!")
    print(f"ID: {d['id']} | Nome: {d['nome']}")


def atualizar_disciplina():
    if not TOKEN:
        print("⚠️  Você precisa fazer login primeiro.")
        return

    print("\n=== ATUALIZAR DISCIPLINA ===")
    aid = input("ID do aluno: ").strip()
    did = input("ID da disciplina: ").strip()
    nome = input("Novo nome (opcional): ").strip()
    data_cadastro = input("Nova data (YYYY-MM-DD) [opcional]: ").strip()

    payload = {
        "nome": nome or None,
        "data_cadastro": data_cadastro or None,
    }

    try:
        resp = requests.put(
            f"{BASE_URL}/students/{aid}/courses/{did}",
            headers=_auth_headers(),
            json=payload,
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"❌ Erro na atualização: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Erro ao atualizar: {resp.status_code} {resp.text}")
        return

    d = resp.json()
    print("✅ Disciplina atualizada!")
    print(f"ID: {d['id']} | Nome: {d['nome']}")


def remover_disciplina():
    if not TOKEN:
        print("⚠️  Você precisa fazer login primeiro.")
        return

    print("\n=== REMOVER DISCIPLINA ===")
    aid = input("ID do aluno: ").strip()
    did = input("ID da disciplina: ").strip()

    try:
        resp = requests.delete(
            f"{BASE_URL}/students/{aid}/courses/{did}",
            headers=_auth_headers(),
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"❌ Erro ao remover: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Erro: {resp.status_code} {resp.text}")
        return

    print("✅ Disciplina removida!")


def listar_disciplinas_aluno():
    if not TOKEN:
        print("⚠️  Faça login primeiro.")
        return

    print("\n=== DISCIPLINAS DO ALUNO ===")
    aid = input("ID do aluno: ").strip()

    # Buscar lista de alunos para descobrir o nome do aluno
    try:
        resp_aluno = requests.get(
            f"{BASE_URL}/students",
            headers=_auth_headers(),
            timeout=5
        )
    except requests.RequestException as e:
        print(f"❌ Erro ao conectar para buscar alunos: {e}")
        return

    if resp_aluno.status_code != 200:
        print(f"❌ Erro ao buscar alunos: {resp_aluno.status_code} {resp_aluno.text}")
        return

    alunos = resp_aluno.json()
    aluno = next((a for a in alunos if a["id"] == aid), None)

    if not aluno:
        print("❌ Aluno não encontrado.")
        return

    print(f"\nAluno: {aluno['nome']} ({aluno['tipo_id']} {aluno['identificador']})")

    # Buscar disciplinas do aluno
    try:
        resp = requests.get(
            f"{BASE_URL}/students/{aid}/courses",
            headers=_auth_headers(),
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"❌ Erro ao listar disciplinas: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Erro ao listar disciplinas: {resp.status_code} {resp.text}")
        return

    disciplinas = resp.json()

    if not disciplinas:
        print("\nNenhuma disciplina cadastrada para este aluno.")
        return

    print("\n=== DISCIPLINAS ===")
    for i, d in enumerate(disciplinas, start=1):
        print(f"{i}) {d['nome']}")
        print(f"    Status: {d['status']}")
        print(f"    Média: {d['media']}")
        print(f"    ID da disciplina: {d['id']}")
        print("-" * 40)

    # Permitir que o usuário escolha uma disciplina para ver detalhes
    print("\nDigite o número da disciplina para ver detalhes (ou Enter para voltar):")
    escolha = input("> ").strip()

    if escolha == "":
        return

    try:
        escolha = int(escolha)
    except ValueError:
        print("Opção inválida.")
        return

    if not (1 <= escolha <= len(disciplinas)):
        print("Número inválido.")
        return

    d = disciplinas[escolha - 1]

    print("\n=== DETALHES DA DISCIPLINA ===")
    print(f"Nome: {d['nome']}")
    print(f"Cadastro: {d['data_cadastro']}")
    print(f"Notas: {d['notas']}")
    print(f"Média: {d['media']}")
    print(f"Status: {d['status']}")
    print(f"ID: {d['id']}")
    print("-" * 40)


# ------------------------------------------------------------------------------
# NOTAS
# ------------------------------------------------------------------------------
def lancar_nota():
    if not TOKEN:
        print("⚠️ Faça login primeiro.")
        return

    print("\n=== LANÇAR NOTA ===")
    aid = input("ID do aluno: ").strip()
    did = input("ID da disciplina: ").strip()
    estagio = input("Estágio (E1/E2/E3 ou 1/2/3): ").strip().upper()
    nota = float(input("Nota (0 a 10): ").strip())

    payload = {"estagio": estagio, "nota": nota}

    try:
        resp = requests.patch(
            f"{BASE_URL}/students/{aid}/courses/{did}/grade",
            headers=_auth_headers(),
            json=payload,
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"❌ Erro ao lançar nota: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Erro: {resp.status_code} {resp.text}")
        return

    d = resp.json()
    print("✅ Nota lançada!")
    print(f"Notas: {d['notas']}")
    print(f"Média: {d['media']} | Status: {d['status']}")


# ------------------------------------------------------------------------------
# LOGS
# ------------------------------------------------------------------------------
def ver_logs():
    if not TOKEN:
        print("⚠️ Faça login primeiro.")
        return

    print("\n=== LOGS DE AUDITORIA ===")
    aid = input("Filtrar por ID de aluno (opcional): ").strip()

    params = {}
    if aid:
        params["aid"] = aid

    try:
        resp = requests.get(
            f"{BASE_URL}/logs",
            headers=_auth_headers(),
            params=params,
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"❌ Erro ao buscar logs: {e}")
        return

    if resp.status_code != 200:
        print(f"❌ Erro: {resp.status_code} {resp.text}")
        return

    logs = resp.json()
    if not logs:
        print("Nenhum log encontrado.")
        return

    for log in logs:
        print(f"[{log['timestamp']}] {log['action']} (ator: {log['actor']})")
        if log.get("aluno_id"):
            print(f"  Aluno ID: {log['aluno_id']}")
        if log.get("mensagem"):
            print(f"  Mensagem: {log['mensagem']}")
        print("-" * 40)


# ------------------------------------------------------------------------------
# MENU PRINCIPAL
# ------------------------------------------------------------------------------
def main():
    while True:
        print("\n=== CONTROLE ACADÊMICO (CLI) ===")
        print("1) Login")
        print("2) Listar alunos")
        print("3) Criar aluno")
        print("4) Adicionar disciplina a aluno")
        print("5) Lançar nota em disciplina")
        print("6) Listar disciplinas de um aluno")
        print("7) Atualizar disciplina")
        print("8) Remover disciplina")
        print("9) Ver logs de auditoria")
        print("0) Sair")
        op = input("Opção: ").strip()

        if op == "1":
            do_login()
        elif op == "2":
            listar_alunos()
        elif op == "3":
            criar_aluno()
        elif op == "4":
            adicionar_disciplina()
        elif op == "5":
            lancar_nota()
        elif op == "6":
            listar_disciplinas_aluno()
        elif op == "7":
            atualizar_disciplina()
        elif op == "8":
            remover_disciplina()
        elif op == "9":
            ver_logs()
        elif op == "0":
            print("Saindo...")
            break
        else:
            print("❌ Opção inválida.")


if __name__ == "__main__":
    main()
