import os
import json
import uuid
import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

# ---------------------------
# Arquivos de dados (JSON)
# ---------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
ALUNOS_FILE = os.path.join(DATA_DIR, 'alunos.json')
LOGS_FILE = os.path.join(DATA_DIR, 'logs.json')

os.makedirs(DATA_DIR, exist_ok=True)
for fpath, seed in [(ALUNOS_FILE, []), (LOGS_FILE, [])]:
    if not os.path.exists(fpath):
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(seed, f, indent=2, ensure_ascii=False)

# ---------------------------
# Util
# ---------------------------
def _today_iso() -> str:
    return datetime.date.today().isoformat()

def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec='seconds')

def _read_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_json(path: str, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------------------------
# Domínio
# ---------------------------
@dataclass
class Disciplina:
    id: str
    nome: str
    data_cadastro: str
    notas: Dict[str, Optional[float]] = field(default_factory=dict)
    # notas = {'E1': float|None, 'E2': float|None, 'E3': float|None}

    def media(self) -> Optional[float]:
        """Média ponderada: E1=30%, E2=30%, E3=40%. Retorna None se falta nota."""
        if any(self.notas.get(e) is None for e in ('E1', 'E2', 'E3')):
            return None
        m = round(
            (float(self.notas['E1']) * 0.30) +
            (float(self.notas['E2']) * 0.30) +
            (float(self.notas['E3']) * 0.40),
            2
        )
        return m

    def status(self) -> str:
        """APROVADO se média >= 7.0; REPROVADO se média < 7.0; EM_CURSO se incompleta."""
        m = self.media()
        if m is None:
            return 'EM_CURSO'
        return 'APROVADO' if m >= 7.0 else 'REPROVADO'


@dataclass
class Aluno:
    id: str
    nome: str
    tipo_id: str              # "MATRICULA" | "CPF"
    identificador: str        # número (sem máscara para CPF, por ex.)
    data_cadastro: str
    ativo: bool = True
    disciplinas: List[Disciplina] = field(default_factory=list)

# ---------------------------
# Conversão para JSON
# ---------------------------
def _to_dict_aluno(a: Aluno) -> Dict[str, Any]:
    return {
        'id': a.id,
        'nome': a.nome,
        'tipo_id': a.tipo_id,
        'identificador': a.identificador,
        'data_cadastro': a.data_cadastro,
        'ativo': a.ativo,
        'disciplinas': [
            {
                'id': d.id,
                'nome': d.nome,
                'data_cadastro': d.data_cadastro,
                'notas': d.notas
            } for d in a.disciplinas
        ],
    }

def _from_dict_aluno(obj: Dict[str, Any]) -> Aluno:
    return Aluno(
        id=obj['id'],
        nome=obj['nome'],
        tipo_id=obj['tipo_id'],
        identificador=obj['identificador'],
        data_cadastro=obj.get('data_cadastro') or _today_iso(),
        ativo=bool(obj.get('ativo', True)),
        disciplinas=[
            Disciplina(
                id=d['id'],
                nome=d['nome'],
                data_cadastro=d.get('data_cadastro') or _today_iso(),
                notas=d.get('notas', {'E1': None, 'E2': None, 'E3': None})
            ) for d in obj.get('disciplinas', [])
        ]
    )

# ---------------------------
# Persistência
# ---------------------------
def _load_alunos() -> List[Aluno]:
    return [_from_dict_aluno(x) for x in _read_json(ALUNOS_FILE)]

def _save_alunos(items: List[Aluno]):
    _write_json(ALUNOS_FILE, [_to_dict_aluno(x) for x in items])

def _append_log(action: str, actor: str = 'admin', aluno_id: Optional[str] = None, **details):
    logs = _read_json(LOGS_FILE)
    logs.append({
        'id': str(uuid.uuid4()),
        'timestamp': _now_iso(),
        'actor': actor,
        'action': action,
        'aluno_id': aluno_id,
        'details': details or {}
    })
    _write_json(LOGS_FILE, logs)

# ---------------------------
# Logs (consulta)
# ---------------------------
def list_logs(aid: Optional[str] = None, limit: int = 100):
    logs = _read_json(LOGS_FILE)
    if aid:
        logs = [x for x in logs if x.get('aluno_id') == aid]
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    return logs[:limit]

# ---------------------------
# Alunos (CRUD)
# ---------------------------
def list_alunos() -> List[Aluno]:
    return _load_alunos()

def filter_alunos(
    name: Optional[str],
    tipo: Optional[str],
    ident: Optional[str],
    date_min: Optional[str],
    date_max: Optional[str]
) -> List[Aluno]:
    items = _load_alunos()
    if name:
        items = [a for a in items if name.lower() in a.nome.lower()]
    if tipo:
        items = [a for a in items if a.tipo_id == tipo]
    if ident:
        items = [a for a in items if a.identificador == ident]
    if date_min:
        items = [a for a in items if a.data_cadastro >= date_min]
    if date_max:
        items = [a for a in items if a.data_cadastro <= date_max]
    return items

def find_aluno(aid: str) -> Aluno:
    for a in _load_alunos():
        if a.id == aid:
            return a
    raise ValueError('Aluno não encontrado')

def _ensure_unique(tipo_id: str, identificador: str):
    for a in _load_alunos():
        if a.tipo_id == tipo_id and a.identificador == identificador:
            raise ValueError(f'{tipo_id} já cadastrado')

def create_aluno(
    nome: str,
    tipo_id: str,
    identificador: str,
    data_cadastro: Optional[str] = None,
    ativo: bool = True
) -> Aluno:
    _ensure_unique(tipo_id, identificador)
    a = Aluno(
        id=str(uuid.uuid4()),
        nome=nome,
        tipo_id=tipo_id,
        identificador=identificador,
        data_cadastro=data_cadastro or _today_iso(),
        ativo=bool(ativo),
        disciplinas=[]
    )
    items = _load_alunos()
    items.insert(0, a)
    _save_alunos(items)
    _append_log('ALUNO_CRIADO', aluno_id=a.id, nome=nome, tipo_id=tipo_id, identificador=identificador, ativo=a.ativo)
    return a

def update_aluno(
    aid: str,
    nome: Optional[str] = None,
    tipo_id: Optional[str] = None,
    identificador: Optional[str] = None,
    data_cadastro: Optional[str] = None,
    ativo: Optional[bool] = None
) -> Aluno:
    items = _load_alunos()
    for i, a in enumerate(items):
        if a.id == aid:
            if nome is not None:
                a.nome = nome
            if tipo_id is not None:
                a.tipo_id = tipo_id
            if identificador is not None:
                a.identificador = identificador
            if data_cadastro is not None:
                a.data_cadastro = data_cadastro
            if ativo is not None:
                a.ativo = bool(ativo)
            items[i] = a
            _save_alunos(items)
            _append_log('ALUNO_ATUALIZADO', aluno_id=aid, fields={
                'nome': nome,
                'tipo_id': tipo_id,
                'identificador': identificador,
                'data_cadastro': data_cadastro,
                'ativo': ativo
            })
            return a
    raise ValueError('Aluno não encontrado')

def delete_aluno(aid: str):
    items = _load_alunos()
    new_items = [a for a in items if a.id != aid]
    if len(new_items) == len(items):
        raise ValueError('Aluno não encontrado')
    _save_alunos(new_items)
    _append_log('ALUNO_REMOVIDO', aluno_id=aid)

def set_aluno_status(aid: str, ativo: bool) -> Aluno:
    a = update_aluno(aid, ativo=ativo)
    _append_log('ALUNO_STATUS_ALTERADO', aluno_id=aid, ativo=ativo)
    return a

# ---------------------------
# Disciplinas (CRUD + notas)
# ---------------------------
def add_disciplina(aid: str, nome: str, data_cadastro: Optional[str] = None) -> Disciplina:
    items = _load_alunos()
    for i, a in enumerate(items):
        if a.id == aid:
            d = Disciplina(
                id=str(uuid.uuid4()),
                nome=nome,
                data_cadastro=data_cadastro or _today_iso(),
                notas={'E1': None, 'E2': None, 'E3': None}
            )
            a.disciplinas.insert(0, d)
            items[i] = a
            _save_alunos(items)
            _append_log('DISCIPLINA_CRIADA', aluno_id=aid, disciplina_id=d.id, nome=nome)
            return d
    raise ValueError('Aluno não encontrado')

def update_disciplina(aid: str, did: str, nome: Optional[str] = None, data_cadastro: Optional[str] = None) -> Disciplina:
    items = _load_alunos()
    for i, a in enumerate(items):
        if a.id != aid:
            continue
        for j, d in enumerate(a.disciplinas):
            if d.id == did:
                if nome is not None:
                    d.nome = nome
                if data_cadastro is not None:
                    d.data_cadastro = data_cadastro
                a.disciplinas[j] = d
                items[i] = a
                _save_alunos(items)
                _append_log('DISCIPLINA_ATUALIZADA', aluno_id=aid, disciplina_id=did, nome=nome, data_cadastro=data_cadastro)
                return d
    raise ValueError('Disciplina não encontrada')

def del_disciplina(aid: str, did: str):
    items = _load_alunos()
    for i, a in enumerate(items):
        if a.id == aid:
            new_ds = [d for d in a.disciplinas if d.id != did]
            if len(new_ds) == len(a.disciplinas):
                raise ValueError('Disciplina não encontrada')
            a.disciplinas = new_ds
            items[i] = a
            _save_alunos(items)
            _append_log('DISCIPLINA_REMOVIDA', aluno_id=aid, disciplina_id=did)
            return
    raise ValueError('Aluno não encontrado')

def set_nota(aid: str, did: str, estagio: str, nota: float) -> Disciplina:
    if estagio not in ('E1', 'E2', 'E3'):
        raise ValueError('Estágio inválido')
    items = _load_alunos()
    for i, a in enumerate(items):
        if a.id != aid:
            continue
        for j, d in enumerate(a.disciplinas):
            if d.id == did:
                d.notas[estagio] = float(nota)
                a.disciplinas[j] = d
                items[i] = a
                _save_alunos(items)
                _append_log('NOTA_ATUALIZADA', aluno_id=aid, disciplina_id=did, estagio=estagio, nota=nota, media=d.media(), status=d.status())
                return d
    raise ValueError('Disciplina não encontrada')
