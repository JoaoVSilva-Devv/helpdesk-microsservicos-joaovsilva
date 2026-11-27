"""Cria os usuários de exemplo só quando o banco deste serviço está vazio."""
import os

from sqlalchemy.orm import Session

from usuarios import servico
from usuarios.esquemas import UsuarioCriar

SENHA = os.getenv("SENHA_EXEMPLO", "Helpdesk2026")

# Ordem estável: ids 1..5 (admin, ana, bruno, carla, diego).
CONTAS = [
    ("Admin TI", "admin@empresa.com", "admin"),
    ("Ana Souza", "ana@empresa.com", "solicitante"),
    ("Bruno Lima", "bruno@empresa.com", "solicitante"),
    ("Carla Dias", "carla@empresa.com", "tecnico"),
    ("Diego Rocha", "diego@empresa.com", "tecnico"),
]


def carregar(db: Session) -> None:
    if servico.listar(db):
        return
    for nome, email, perfil in CONTAS:
        servico.criar(db, UsuarioCriar(nome=nome, email=email, perfil=perfil, senha=SENHA))
