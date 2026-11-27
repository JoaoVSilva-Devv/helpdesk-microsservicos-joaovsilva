import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from usuarios import database
from usuarios import servico
from usuarios.auth import limite
from usuarios.esquemas import UsuarioCriar
from usuarios.main import app

SENHA = "Senha123"


@pytest.fixture
def sessao():
    """Banco novo, em memória, para cada teste."""
    limite.limpar_tudo()
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
def contas(sessao, cliente):
    """Cria admin, dois solicitantes e uma técnica; devolve cabeçalhos e ids."""
    with sessao() as db:
        for nome, email, perfil in [("Admin", "admin@x.com", "admin"), ("Ana", "ana@x.com", "solicitante"),
                                    ("Bia", "bia@x.com", "solicitante"), ("Carla", "carla@x.com", "tecnico")]:
            servico.criar(db, UsuarioCriar(nome=nome, email=email, perfil=perfil, senha=SENHA))
    resultado = {}
    for apelido in ("admin", "ana", "bia", "carla"):
        r = cliente.post("/auth/login", json={"email": f"{apelido}@x.com", "senha": SENHA})
        assert r.status_code == 200, r.text
        resultado[apelido] = {"headers": {"Authorization": f"Bearer {r.json()['access_token']}"},
                              "id": r.json()["usuario"]["id"]}
    return resultado
