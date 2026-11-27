"""Integração dos três serviços em memória.

Os chamados falam com os outros serviços pela mesma função HTTP (`clientes._get`),
que aqui é substituída por TestClient. Assim os testes exercitam as rotas reais,
inclusive o repasse do token, sem precisar subir o Docker.
"""
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from usuarios import database as db_usuarios
from usuarios import servico as servico_usuarios
from usuarios.auth import limite
from usuarios.esquemas import UsuarioCriar
from usuarios.main import app as app_usuarios

from inventario import database as db_inventario
from inventario import servico as servico_inventario
from inventario.esquemas import AtivoCriar
from inventario.main import app as app_inventario

from chamados import clientes
from chamados import database as db_chamados
from chamados.main import app as app_chamados

SENHA = "Senha123"


def _banco(pacote):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    pacote.Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def infra(monkeypatch):
    limite.limpar_tudo()
    SessaoUsuarios = _banco(db_usuarios)
    SessaoInventario = _banco(db_inventario)
    SessaoChamados = _banco(db_chamados)
    tokens_vistos = []

    def override(Sessao):
        def get_db():
            db = Sessao()
            try:
                yield db
            finally:
                db.close()
        return get_db

    for app, pacote, Sessao in [
        (app_usuarios, db_usuarios, SessaoUsuarios),
        (app_inventario, db_inventario, SessaoInventario),
        (app_chamados, db_chamados, SessaoChamados),
    ]:
        app.dependency_overrides[pacote.get_db] = override(Sessao)

    with TestClient(app_usuarios) as c_usuarios, TestClient(app_inventario) as c_inventario, \
            TestClient(app_chamados) as c_chamados:
        with SessaoUsuarios() as db:
            for nome, email, perfil in [("Admin", "admin@x.com", "admin"), ("Ana", "ana@x.com", "solicitante"),
                                        ("Bia", "bia@x.com", "solicitante"), ("Carla", "carla@x.com", "tecnico")]:
                servico_usuarios.criar(db, UsuarioCriar(nome=nome, email=email, perfil=perfil, senha=SENHA))
        contas = {}
        for apelido in ("admin", "ana", "bia", "carla"):
            r = c_usuarios.post("/auth/login", json={"email": f"{apelido}@x.com", "senha": SENHA})
            assert r.status_code == 200, r.text
            contas[apelido] = {"headers": {"Authorization": f"Bearer {r.json()['access_token']}"},
                               "id": r.json()["usuario"]["id"]}

        with SessaoInventario() as db:
            ativo = servico_inventario.criar(
                db, AtivoCriar(patrimonio="PAT-1", tipo="computador", descricao="Desktop", setor="TI"))

        def get_http(url, token):
            tokens_vistos.append(token)
            caminho = urlparse(url).path
            if "/usuarios/" in caminho:
                return c_usuarios.get(caminho, headers={"Authorization": token})
            if "/ativos/" in caminho:
                return c_inventario.get(caminho, headers={"Authorization": token})
            raise AssertionError(f"URL inesperada: {url}")

        monkeypatch.setattr(clientes, "_get", get_http)

        yield {
            "usuarios": c_usuarios, "inventario": c_inventario, "chamados": c_chamados,
            "sessoes": (SessaoUsuarios, SessaoInventario, SessaoChamados),
            "contas": contas, "ativo": ativo, "tokens_vistos": tokens_vistos,
        }

    for app in (app_usuarios, app_inventario, app_chamados):
        app.dependency_overrides.clear()
