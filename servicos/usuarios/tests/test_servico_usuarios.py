"""Testes do serviço de Usuários (login, tokens e permissões)."""
from datetime import datetime, timedelta, timezone

import jwt

from usuarios import config

SENHA = "Senha123"


def test_login_e_auth_eu(cliente, contas):
    r = cliente.get("/auth/eu", headers=contas["carla"]["headers"])
    assert r.status_code == 200 and r.json()["email"] == "carla@x.com"


def test_login_com_senha_errada_e_email_inexistente(cliente, contas):
    for email in ("ana@x.com", "ninguem@x.com"):
        r = cliente.post("/auth/login", json={"email": email, "senha": "errada123"})
        assert r.status_code == 401 and r.json()["detail"] == "E-mail ou senha inválidos."


def test_bloqueio_apos_varias_falhas(cliente, contas):
    for _ in range(config.LOGIN_MAX_FALHAS):
        cliente.post("/auth/login", json={"email": "ana@x.com", "senha": "errada123"})
    assert cliente.post("/auth/login", json={"email": "ana@x.com", "senha": SENHA}).status_code == 429


def test_token_adulterado_e_outro_segredo(cliente, contas):
    assert cliente.get("/auth/eu", headers={"Authorization": contas["ana"]["headers"]["Authorization"] + "x"}).status_code == 401
    falso = jwt.encode(
        {"sub": str(contas["admin"]["id"]), "perfil": "admin", "iss": config.JWT_EMISSOR,
         "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "segredo-de-outra-pessoa-com-mais-de-32-caracteres", algorithm="HS256",
    )
    assert cliente.get("/auth/eu", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_sem_assinatura_e_vencido(cliente, contas):
    base = {"sub": str(contas["admin"]["id"]), "perfil": "admin", "iss": config.JWT_EMISSOR}
    sem_assinatura = jwt.encode({**base, "iat": datetime.now(timezone.utc),
                                 "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, None, algorithm="none")
    antigo = datetime.now(timezone.utc) - timedelta(hours=2)
    vencido = jwt.encode({**base, "iat": antigo, "exp": antigo + timedelta(minutes=5)},
                         config.JWT_SEGREDO, algorithm="HS256")
    assert cliente.get("/auth/eu", headers={"Authorization": f"Bearer {sem_assinatura}"}).status_code == 401
    assert cliente.get("/auth/eu", headers={"Authorization": f"Bearer {vencido}"}).status_code == 401


def test_rotas_exigem_token(cliente, contas):
    for metodo, rota in [("get", "/auth/eu"), ("get", "/usuarios"), ("get", "/usuarios/1"),
                         ("post", "/usuarios")]:
        assert getattr(cliente, metodo)(rota).status_code == 401, rota


def test_admin_cria_usuario_sem_devolver_senha(cliente, contas):
    r = cliente.post("/usuarios", headers=contas["admin"]["headers"],
                     json={"nome": "Davi", "email": "davi@x.com", "perfil": "tecnico", "senha": "Forte1234"})
    assert r.status_code == 201 and "senha" not in r.json() and "senha_hash" not in r.json()


def test_solicitante_nao_cria_usuario(cliente, contas):
    r = cliente.post("/usuarios", headers=contas["ana"]["headers"],
                     json={"nome": "Eva", "email": "eva@x.com", "perfil": "admin", "senha": "Forte1234"})
    assert r.status_code == 403


def test_senha_fraca_email_repetido_e_campos_extras(cliente, contas):
    assert cliente.post("/usuarios", headers=contas["admin"]["headers"],
                        json={"nome": "Eva", "email": "eva@x.com", "perfil": "admin", "senha": "abcdefgh"}).status_code == 422
    assert cliente.post("/usuarios", headers=contas["admin"]["headers"],
                        json={"nome": "Ana 2", "email": "ANA@x.com", "perfil": "admin", "senha": "Forte1234"}).status_code == 422
    assert cliente.post("/usuarios", headers=contas["admin"]["headers"],
                        json={"nome": "Eva", "email": "eva@x.com", "perfil": "admin", "senha": "Forte1234", "admin": True}).status_code == 422


def test_lista_publica_nao_mostra_email_e_404(cliente, contas):
    lista = cliente.get("/usuarios", headers=contas["ana"]["headers"]).json()
    assert lista and all("email" not in u for u in lista)
    assert cliente.get("/usuarios/99", headers=contas["ana"]["headers"]).status_code == 404


def test_senha_guardada_com_hash(sessao, contas):
    from usuarios.modelos import Usuario
    with sessao() as db:
        u = db.query(Usuario).filter_by(email="ana@x.com").one()
        assert SENHA not in u.senha_hash and u.senha_hash.startswith("scrypt$")


def test_saude(cliente):
    assert cliente.get("/saude").json() == {"status": "ok", "servico": "usuarios"}
