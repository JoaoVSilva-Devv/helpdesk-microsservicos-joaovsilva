"""Chamados de exemplo no banco deste serviço.

Os ids seguem a ordem dos dados de exemplo dos outros serviços (Ana=2,
Bruno=3, Carla=4; ativos 1 e 2). Como não há FK entre serviços, este serviço
consegue criar seus exemplos mesmo se os outros ainda não estiverem no ar.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from chamados import repositorio
from chamados.modelos import Chamado
from chamados.notificacoes import servico as notificacoes
from chamados.servico import calcular_prazo

EXEMPLOS = [
    ("Computador não liga", "Apertei o botão e nada acontece.", "alta", 1, 2, 4),
    ("Impressora atolando papel", "Atola a cada 3 folhas.", "media", 2, 3, None),
    ("Acesso ao sistema de RH", "Preciso de acesso para a nova estagiária.", "baixa", None, 3, None),
]


def carregar(db: Session) -> None:
    if repositorio.listar(db):
        return
    for titulo, descricao, prioridade, ativo_id, solicitante_id, tecnico_id in EXEMPLOS:
        agora = datetime.now()
        chamado = repositorio.salvar(db, Chamado(
            titulo=titulo, descricao=descricao, prioridade=prioridade, ativo_id=ativo_id,
            solicitante_id=solicitante_id, tecnico_id=tecnico_id,
            status="em_atendimento" if tecnico_id else "aberto",
            criado_em=agora, prazo_sla=calcular_prazo(prioridade, agora),
        ))
        notificacoes.notificar(db, "ChamadoAberto", solicitante_id,
                               f"Seu chamado #{chamado.id} foi aberto. Prazo: {chamado.prazo_sla:%d/%m %H:%M}.")
        if tecnico_id:
            notificacoes.notificar(db, "ChamadoAtribuido", tecnico_id,
                                   f"O chamado #{chamado.id} foi atribuído a você.")
