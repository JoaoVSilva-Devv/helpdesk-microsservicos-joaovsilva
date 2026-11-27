"""Avisos gerados pelos eventos de chamado (no próprio banco do serviço)."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from chamados.notificacoes.modelos import Notificacao


def notificar(db: Session, tipo: str, destinatario_id: int, mensagem: str) -> Notificacao:
    aviso = Notificacao(tipo=tipo, destinatario_id=destinatario_id, mensagem=mensagem,
                        criada_em=datetime.now())
    db.add(aviso)
    db.commit()
    db.refresh(aviso)
    return aviso


def listar(db: Session, destinatario_id: int | None = None) -> list[Notificacao]:
    consulta = select(Notificacao).order_by(Notificacao.id)
    if destinatario_id:
        consulta = consulta.where(Notificacao.destinatario_id == destinatario_id)
    return list(db.scalars(consulta))
