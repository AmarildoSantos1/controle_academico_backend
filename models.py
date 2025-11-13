from pydantic import BaseModel, Field
from typing import Optional, Dict, List

# ---------------------------
# Auth
# ---------------------------
class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    token: str

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


# ---------------------------
# Disciplinas / Notas
# ---------------------------
class DisciplinaIn(BaseModel):
    nome: str
    data_cadastro: Optional[str] = None  # YYYY-MM-DD opcional

class NotaIn(BaseModel):
    estagio: str  # 'E1' | 'E2' | 'E3'
    nota: float   # 0..10 (não validamos range aqui; regra fica no domínio)

class DisciplinaOut(BaseModel):
    id: str
    nome: str
    data_cadastro: str
    notas: Dict[str, Optional[float]]  # {'E1': float|None, 'E2':..., 'E3':...}
    media: Optional[float]             # média ponderada 0..10 ou None se incompleta
    status: str                        # 'EM_CURSO' | 'APROVADO' | 'REPROVADO'


# ---------------------------
# Alunos
# ---------------------------
class AlunoIn(BaseModel):
    nome: str
    tipo_id: str              # "MATRICULA" | "CPF"
    identificador: str        # número da matrícula/CPF (sem máscara)
    data_cadastro: Optional[str] = None  # YYYY-MM-DD opcional
    ativo: Optional[bool] = True         # default: True

class AlunoOut(BaseModel):
    id: str
    nome: str
    tipo_id: str
    identificador: str
    data_cadastro: str
    ativo: bool
    disciplinas: List[DisciplinaOut] = Field(default_factory=list)


# ---------------------------
# Alteração de status
# ---------------------------
class StatusIn(BaseModel):
    ativo: bool


# ---------------------------
# Logs
# ---------------------------
class LogOut(BaseModel):
    id: str
    timestamp: str
    actor: str
    action: str
    aluno_id: Optional[str] = None
    details: dict = Field(default_factory=dict)
