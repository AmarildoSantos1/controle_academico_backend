from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional, List
from io import StringIO
import csv

from auth import ensure_admin, verify_user, issue_token, validate_token, revoke_token, change_password
from models import LoginIn, TokenOut, ChangePasswordIn, AlunoIn, AlunoOut, DisciplinaIn, DisciplinaOut, NotaIn, StatusIn, LogOut
import storage as db
from util import nonempty

app = FastAPI(title="Controle Acadêmico API", version="2.0.0")
ensure_admin()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {'ok': True, 'service': 'Controle Acadêmico API', 'docs': '/docs'}

def require_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Token ausente')
    token = authorization.split(' ', 1)[1]
    if not validate_token(token):
        raise HTTPException(401, 'Token inválido ou expirado')
    return token

# ---------- AUTH ----------
@app.post('/auth/login', response_model=TokenOut)
def login(payload: LoginIn):
    if not verify_user(payload.username, payload.password):
        raise HTTPException(401, 'Credenciais inválidas')
    return TokenOut(token=issue_token())

@app.post('/auth/logout')
def logout(token: str = Depends(require_token)):
    revoke_token(token)
    return {'ok': True}

@app.post('/auth/change-password')
def change_pwd(body: ChangePasswordIn, token: str = Depends(require_token)):
    try:
        change_password(body.old_password, body.new_password)
        revoke_token(token)
        return {'ok': True, 'message': 'Senha alterada. Faça login novamente.'}
    except ValueError as e:
        raise HTTPException(400, str(e))

# ---------- STUDENTS ----------
@app.get('/students', response_model=List[AlunoOut])
def list_students(
    name: Optional[str] = None,
    tipo: Optional[str] = None,
    ident: Optional[str] = None,
    date_min: Optional[str] = None,
    date_max: Optional[str] = None,
    token: str = Depends(require_token)
):
    items = db.filter_alunos(nonempty(name), nonempty(tipo), nonempty(ident), nonempty(date_min), nonempty(date_max))
    return [
        AlunoOut(
            id=a.id,
            nome=a.nome,
            tipo_id=a.tipo_id,
            identificador=a.identificador,
            data_cadastro=a.data_cadastro,
            ativo=a.ativo,
            disciplinas=[
                DisciplinaOut(
                    id=d.id,
                    nome=d.nome,
                    data_cadastro=d.data_cadastro,
                    notas=d.notas,
                    media=d.media(),
                    status=d.status()
                )
                for d in a.disciplinas
            ],
        )
        for a in items
    ]

@app.post('/students', response_model=AlunoOut)
def create_student(body: AlunoIn, token: str = Depends(require_token)):
    try:
        a = db.create_aluno(
            body.nome, body.tipo_id, body.identificador, body.data_cadastro,
            ativo=(True if body.ativo is None else body.ativo)
        )
        return AlunoOut(
            id=a.id,
            nome=a.nome,
            tipo_id=a.tipo_id,
            identificador=a.identificador,
            data_cadastro=a.data_cadastro,
            ativo=a.ativo,
            disciplinas=[]
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.put('/students/{aid}', response_model=AlunoOut)
def update_student(aid: str, body: AlunoIn, token: str = Depends(require_token)):
    try:
        a = db.update_aluno(
            aid,
            nome=body.nome,
            tipo_id=body.tipo_id,
            identificador=body.identificador,
            data_cadastro=body.data_cadastro,
            ativo=body.ativo
        )
        return AlunoOut(
            id=a.id,
            nome=a.nome,
            tipo_id=a.tipo_id,
            identificador=a.identificador,
            data_cadastro=a.data_cadastro,
            ativo=a.ativo,
            disciplinas=[
                DisciplinaOut(
                    id=d.id,
                    nome=d.nome,
                    data_cadastro=d.data_cadastro,
                    notas=d.notas,
                    media=d.media(),
                    status=d.status()
                )
                for d in a.disciplinas
            ],
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.delete('/students/{aid}')
def delete_student(aid: str, token: str = Depends(require_token)):
    try:
        db.delete_aluno(aid)
        return {'ok': True}
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.patch('/students/{aid}/status', response_model=AlunoOut)
def set_status(aid: str, body: StatusIn, token: str = Depends(require_token)):
    try:
        a = db.set_aluno_status(aid, body.ativo)
        return AlunoOut(
            id=a.id,
            nome=a.nome,
            tipo_id=a.tipo_id,
            identificador=a.identificador,
            data_cadastro=a.data_cadastro,
            ativo=a.ativo,
            disciplinas=[
                DisciplinaOut(
                    id=d.id,
                    nome=d.nome,
                    data_cadastro=d.data_cadastro,
                    notas=d.notas,
                    media=d.media(),
                    status=d.status()
                )
                for d in a.disciplinas
            ],
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

# ---------- COURSES ----------
@app.get('/students/{aid}/courses', response_model=List[DisciplinaOut])
def list_courses(aid: str, name: Optional[str] = None, stage_with_grade: Optional[str] = None, date_min: Optional[str] = None, date_max: Optional[str] = None, token: str = Depends(require_token)):
    a = db.find_aluno(aid)
    ds = a.disciplinas
    if nonempty(name):
        ds = [d for d in ds if name.lower() in d.nome.lower()]
    if nonempty(stage_with_grade):
        e = stage_with_grade.upper().replace('1', 'E1').replace('2', 'E2').replace('3', 'E3')
        if e not in ('E1', 'E2', 'E3'):
            raise HTTPException(400, 'Estágio inválido')
        ds = [d for d in ds if d.notas.get(e) is not None]
    from util import to_date, ensure_date
    if nonempty(date_min):
        ensure_date(date_min)
        ds = [d for d in ds if to_date(d.data_cadastro) >= to_date(date_min)]
    if nonempty(date_max):
        ensure_date(date_max)
        ds = [d for d in ds if to_date(d.data_cadastro) <= to_date(date_max)]
    return [
        DisciplinaOut(
            id=d.id,
            nome=d.nome,
            data_cadastro=d.data_cadastro,
            notas=d.notas,
            media=d.media(),
            status=d.status()
        )
        for d in ds
    ]

@app.post('/students/{aid}/courses', response_model=DisciplinaOut)
def create_course(aid: str, body: DisciplinaIn, token: str = Depends(require_token)):
    try:
        d = db.add_disciplina(aid, body.nome, body.data_cadastro)
        return DisciplinaOut(id=d.id, nome=d.nome, data_cadastro=d.data_cadastro, notas=d.notas, media=d.media(), status=d.status())
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.put('/students/{aid}/courses/{did}', response_model=DisciplinaOut)
def update_course(aid: str, did: str, body: DisciplinaIn, token: str = Depends(require_token)):
    try:
        d = db.update_disciplina(aid, did, nome=body.nome, data_cadastro=body.data_cadastro)
        return DisciplinaOut(id=d.id, nome=d.nome, data_cadastro=d.data_cadastro, notas=d.notas, media=d.media(), status=d.status())
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.delete('/students/{aid}/courses/{did}')
def delete_course(aid: str, did: str, token: str = Depends(require_token)):
    try:
        db.del_disciplina(aid, did)
        return {'ok': True}
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.patch('/students/{aid}/courses/{did}/grade', response_model=DisciplinaOut)
def set_grade(aid: str, did: str, body: NotaIn, token: str = Depends(require_token)):
    try:
        d = db.set_nota(aid, did, body.estagio, body.nota)
        return DisciplinaOut(id=d.id, nome=d.nome, data_cadastro=d.data_cadastro, notas=d.notas, media=d.media(), status=d.status())
    except ValueError as e:
        raise HTTPException(400, str(e))

# ---------- CSV ----------
@app.get('/students/{aid}/report.csv')
def aluno_csv(aid: str, token: str = Depends(require_token)):
    a = db.find_aluno(aid)
    sio = StringIO()
    w = csv.writer(sio)
    w.writerow(['Aluno', a.nome])
    w.writerow(['Identificador', f'{a.tipo_id}: {a.identificador}'])
    w.writerow(['Cadastro', a.data_cadastro])
    w.writerow(['Ativo', 'SIM' if a.ativo else 'NÃO'])
    w.writerow([])
    w.writerow(['ID Disciplina','Nome','E1','E2','E3','Média','Status','Cadastro'])
    for d in a.disciplinas:
        w.writerow([d.id, d.nome, d.notas.get('E1'), d.notas.get('E2'), d.notas.get('E3'), d.media(), d.status(), d.data_cadastro])
    sio.seek(0)
    return StreamingResponse(iter([sio.getvalue()]), media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="boletim_{a.identificador}.csv"'})

@app.get('/reports/class.csv')
def turma_csv(token: str = Depends(require_token)):
    alunos = db.list_alunos()
    sio = StringIO()
    w = csv.writer(sio)
    w.writerow(['Aluno','Tipo','Identificador','Ativo','Disciplina','E1','E2','E3','Média','Status','Cadastro'])
    for a in alunos:
        if not a.disciplinas:
            w.writerow([a.nome,a.tipo_id,a.identificador,'SIM' if a.ativo else 'NÃO','(sem disciplinas)','','','','','EM CURSO',a.data_cadastro])
        for d in a.disciplinas:
            w.writerow([a.nome,a.tipo_id,a.identificador,'SIM' if a.ativo else 'NÃO',d.nome,d.notas.get('E1'),d.notas.get('E2'),d.notas.get('E3'),d.media(),d.status(),d.data_cadastro])
    sio.seek(0)
    return StreamingResponse(iter([sio.getvalue()]), media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="relatorio_turma.csv"'})

# ---------- LOGS ----------
@app.get('/logs', response_model=List[LogOut])
def get_logs(aid: Optional[str] = None, limit: int = 100, token: str = Depends(require_token)):
    rows = db.list_logs(aid, limit)
    return rows
