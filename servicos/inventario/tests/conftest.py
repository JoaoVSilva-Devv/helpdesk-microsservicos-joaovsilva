from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from inventario import config, database
from inventario import servico
from inventario.esquemas import AtivoCriar
from inventario.main import app


def criar_token(usuario_id: int, perfil: str) -> str:
    agora = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(usuario_id), "perfil": perfil, "iat": agora,
         "exp": agora + timedelta(hours=1), "iss": config.JWT_EMISSOR},
        config.JWT_SEGREDO, algorithm=config.JWT_ALGORITMO,
    )


@pytest.fixture
def sessao():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def db_de_teste():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[database.get_db] = db_de_teste
    yield Sessao
    app.dependency_overrides.clear()


@pytest.fixture
def cliente(sessao):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def contas():
    """Tokens assinados com o segredo compartilhado, como se viessem do login."""
    perfis = {"admin": "admin", "carla": "tecnico", "ana": "solicitante"}
    return {
        apelido: {"headers": {"Authorization": f"Bearer {criar_token(i, perfil)}"}, "id": i}
        for i, (apelido, perfil) in enumerate(perfis.items(), start=1)
    }


@pytest.fixture
def ativo(sessao):
    with sessao() as db:
        return servico.criar(db, AtivoCriar(patrimonio="PAT-1", tipo="computador", descricao="Desktop", setor="TI"))
