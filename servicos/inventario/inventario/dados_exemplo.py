"""Cria os equipamentos de exemplo só quando o banco deste serviço está vazio."""
from sqlalchemy.orm import Session

from inventario import servico
from inventario.esquemas import AtivoCriar

ATIVOS = [
    ("PAT-0001", "computador", "Desktop Dell OptiPlex", "Financeiro"),
    ("PAT-0002", "impressora", "Impressora HP LaserJet", "RH"),
    ("PAT-0003", "notebook", "Notebook Lenovo ThinkPad", "TI"),
]


def carregar(db: Session) -> None:
    if servico.listar(db):
        return
    for patrimonio, tipo, descricao, setor in ATIVOS:
        servico.criar(db, AtivoCriar(patrimonio=patrimonio, tipo=tipo, descricao=descricao, setor=setor))
