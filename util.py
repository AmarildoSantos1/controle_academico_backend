from typing import Optional
from datetime import datetime

def nonempty(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    return s or None

def ensure_date(s: str):
    """Valida formato YYYY-MM-DD. Lança ValueError se inválido."""
    datetime.strptime(s, '%Y-%m-%d')

def to_date(s: str):
    """Converte 'YYYY-MM-DD' para date."""
    return datetime.strptime(s, '%Y-%m-%d').date()
