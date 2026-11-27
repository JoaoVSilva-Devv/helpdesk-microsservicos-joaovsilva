"""Testes do serviço de Inventário."""
from datetime import datetime, timedelta, timezone

import jwt

from inventario import config


def test_tecnico_cadastra_ativo_e_filtra_por_setor(cliente, contas):
    h = contas["carla"]["headers"]
    cliente.post("/ativos", headers=h, json={"patrimonio": "PAT-1", "tipo": "impressora", "descricao": "HP", "setor": "RH"})
    cliente.post("/ativos", headers=h, json={"patrimonio": "PAT-2", "tipo": "computador", "descricao": "Dell", "setor": "TI"})
    assert len(cliente.get("/ativos", params={"setor": "RH"}, headers=h).json()) == 1


def test_solicitante_nao_cadastra_ativo(cliente, contas):
    r = cliente.post("/ativos", headers=contas["ana"]["headers"],
                     json={"patrimonio": "PAT-9", "tipo": "outro", "descricao": "X", "setor": "TI"})
    assert r.status_code == 403


def test_patrimonio_repetido_e_campos_invalidos(cliente, contas):
    h = contas["carla"]["headers"]
    dados = {"patrimonio": "PAT-1", "tipo": "outro", "descricao": "XX", "setor": "TI"}
    assert cliente.post("/ativos", headers=h, json=dados).status_code == 201
    assert cliente.post("/ativos", headers=h, json=dados).status_code == 422
    assert cliente.post("/ativos", headers=h, json={**dados, "patrimonio": "PAT-2", "dono": 1}).status_code == 422


def test_obter_ativo_e_inexistente(cliente, contas, ativo):
    h = contas["carla"]["headers"]
    assert cliente.get(f"/ativos/{ativo.id}", headers=h).json()["patrimonio"] == "PAT-1"
    assert cliente.get("/ativos/999", headers=h).status_code == 404


def test_token_obrigatorio_e_invalido(cliente, contas, ativo):
    assert cliente.get("/ativos").status_code == 401
    assert cliente.get(f"/ativos/{ativo.id}", headers={"Authorization": "Bearer xxx"}).status_code == 401
    falso = jwt.encode(
        {"sub": "1", "perfil": "admin", "iss": config.JWT_EMISSOR,
         "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "outro-segredo-com-mais-de-32-caracteres-aqui", algorithm="HS256",
    )
    assert cliente.get("/ativos", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_saude(cliente):
    assert cliente.get("/saude").json() == {"status": "ok", "servico": "inventario"}
