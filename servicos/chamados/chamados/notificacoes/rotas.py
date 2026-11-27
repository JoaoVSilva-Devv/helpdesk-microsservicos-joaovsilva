from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from chamados.database import get_db
from chamados.notificacoes import servico
from chamados.seguranca_usuario import usuario_atual

router = APIRouter(prefix="/notificacoes", tags=["Notificações"])


class NotificacaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    destinatario_id: int
    mensagem: str
    criada_em: datetime


@router.get("", response_model=list[NotificacaoSaida])
def minhas_notificacoes(usuario=Depends(usuario_atual), db: Session = Depends(get_db)):
    """Cada usuário vê só as próprias notificações."""
    return servico.listar(db, usuario.id)
