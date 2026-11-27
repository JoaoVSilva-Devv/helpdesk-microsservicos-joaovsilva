"""Testes do serviço de Chamados, incluindo comunicação HTTP e falhas."""
from datetime import datetime

import httpx


def abrir(infra, quem="ana", prioridade="alta", **extra):
    dados = {"titulo": "PC não liga", "descricao": "Nada acontece", "prioridade": prioridade,
             "ativo_id": infra["ativo"].id, **extra}
    return infra["chamados"].post("/chamados", headers=infra["contas"][quem]["headers"], json=dados)


def test_abrir_calcula_sla_e_notifica(infra):
    r = abrir(infra, prioridade="critica")
    assert r.status_code == 201
    c = r.json()
    assert c["solicitante_id"] == infra["contas"]["ana"]["id"]
    horas = (datetime.fromisoformat(c["prazo_sla"]) - datetime.fromisoformat(c["criado_em"])).total_seconds() / 3600
    assert round(horas) == 4
    avisos = infra["chamados"].get("/notificacoes", headers=infra["contas"]["ana"]["headers"]).json()
    assert avisos[0]["tipo"] == "ChamadoAberto"


def test_abrir_com_ativo_inexistente(infra):
    assert abrir(infra, ativo_id=999).status_code == 404


def test_token_e_repassado_na_chamada_http(infra):
    infra["tokens_vistos"].clear()
    assert abrir(infra).status_code == 201
    assert infra["tokens_vistos"] == [infra["contas"]["ana"]["headers"]["Authorization"]]


def test_atribuir_confere_tecnico_por_http_e_avisa(infra):
    cid = abrir(infra).json()["id"]
    h = infra["contas"]["carla"]["headers"]
    r = infra["chamados"].patch(f"/chamados/{cid}/atribuir", headers=h,
                                json={"tecnico_id": infra["contas"]["carla"]["id"]})
    assert r.status_code == 200 and r.json()["status"] == "em_atendimento"
    avisos = infra["chamados"].get("/notificacoes", headers=h).json()
    assert avisos[0]["tipo"] == "ChamadoAtribuido"


def test_so_tecnico_pode_ser_atribuido(infra):
    cid = abrir(infra).json()["id"]
    r = infra["chamados"].patch(f"/chamados/{cid}/atribuir", headers=infra["contas"]["carla"]["headers"],
                                json={"tecnico_id": infra["contas"]["ana"]["id"]})
    assert r.status_code == 422


def test_fluxo_completo_de_status(infra):
    cid = abrir(infra).json()["id"]
    tec = infra["contas"]["carla"]["headers"]
    infra["chamados"].patch(f"/chamados/{cid}/atribuir", headers=tec,
                            json={"tecnico_id": infra["contas"]["carla"]["id"]})
    assert infra["chamados"].patch(f"/chamados/{cid}/status", headers=tec,
                                   json={"status": "resolvido"}).status_code == 200
    r = infra["chamados"].patch(f"/chamados/{cid}/status", headers=infra["contas"]["ana"]["headers"],
                                json={"status": "fechado"})
    assert r.json()["status"] == "fechado"


def test_transicoes_e_atribuicao(infra):
    cid = abrir(infra).json()["id"]
    tec = infra["contas"]["carla"]["headers"]
    assert infra["chamados"].patch(f"/chamados/{cid}/status", headers=tec,
                                   json={"status": "fechado"}).status_code == 422
    assert infra["chamados"].patch(f"/chamados/{cid}/status", headers=tec,
                                   json={"status": "em_atendimento"}).status_code == 422


def test_comentar_usa_o_usuario_do_token(infra):
    cid = abrir(infra).json()["id"]
    r = infra["chamados"].post(f"/chamados/{cid}/comentarios", headers=infra["contas"]["carla"]["headers"],
                               json={"texto": "Verificando a fonte."})
    assert r.status_code == 201 and r.json()["autor_id"] == infra["contas"]["carla"]["id"]
    assert len(infra["chamados"].get(f"/chamados/{cid}", headers=infra["contas"]["ana"]["headers"])
               .json()["comentarios"]) == 1


def test_painel_e_filtros(infra):
    abrir(infra)
    abrir(infra, prioridade="baixa")
    p = infra["chamados"].get("/chamados/painel", headers=infra["contas"]["carla"]["headers"]).json()
    assert p["total"] == 2 and p["por_status"] == {"aberto": 2}
    assert len(infra["chamados"].get("/chamados", params={"status": "aberto"},
                                     headers=infra["contas"]["carla"]["headers"]).json()) == 2


def test_permissoes_e_campos_extras(infra):
    c = infra["chamados"]
    ana = infra["contas"]["ana"]["headers"]
    bia = infra["contas"]["bia"]["headers"]
    cid = abrir(infra).json()["id"]
    assert c.get(f"/chamados/{cid}", headers=bia).status_code == 404
    assert c.get("/chamados", headers=bia).json() == []
    assert c.patch(f"/chamados/{cid}/atribuir", headers=ana,
                   json={"tecnico_id": infra["contas"]["carla"]["id"]}).status_code == 403
    assert c.patch(f"/chamados/{cid}/status", headers=ana, json={"status": "em_atendimento"}).status_code == 403
    assert abrir(infra, solicitante_id=infra["contas"]["bia"]["id"]).status_code == 422
    assert c.post(f"/chamados/{cid}/comentarios", headers=ana,
                  json={"texto": "oi", "autor_id": infra["contas"]["carla"]["id"]}).status_code == 422


def test_token_obrigatorio_e_invalido(infra):
    c = infra["chamados"]
    for metodo, rota in [("get", "/chamados"), ("get", "/chamados/painel"), ("post", "/chamados"),
                         ("get", "/notificacoes")]:
        assert getattr(c, metodo)(rota).status_code == 401, rota
    assert c.get("/chamados", headers={"Authorization": "Bearer xxx"}).status_code == 401


def test_notificacoes_sao_so_do_proprio_usuario(infra):
    abrir(infra)
    assert infra["chamados"].get("/notificacoes", headers=infra["contas"]["bia"]["headers"]).json() == []


def test_entrada_e_cabecalhos(infra):
    assert abrir(infra, titulo="x" * 500).status_code == 422
    corpo = '{"titulo": "' + "x" * 70000 + '"}'
    r = infra["chamados"].post("/chamados", headers={**infra["contas"]["ana"]["headers"],
                                                      "Content-Type": "application/json"}, content=corpo)
    assert r.status_code == 413
    assert infra["chamados"].get("/saude").json() == {"status": "ok", "servico": "chamados"}


def test_servico_de_inventario_fora_do_ar_retorna_503(monkeypatch, infra):
    monkeypatch.setattr("chamados.clientes._get", lambda url, token: (_ for _ in ()).throw(
        httpx.ConnectError("inventario fora do ar")))
    r = abrir(infra)
    assert r.status_code == 503 and "Inventário" in r.json()["detail"]
    # O resto do sistema continua funcionando
    assert infra["chamados"].get("/chamados", headers=infra["contas"]["carla"]["headers"]).status_code == 200
    assert infra["chamados"].post("/chamados", headers=infra["contas"]["ana"]["headers"], json={
        "titulo": "Sem equipamento", "descricao": "Teste", "prioridade": "baixa", "ativo_id": None,
    }).status_code == 201


def test_timeout_do_servico_de_usuarios_retorna_503(monkeypatch, infra):
    cid = abrir(infra).json()["id"]
    monkeypatch.setattr("chamados.clientes._get", lambda url, token: (_ for _ in ()).throw(
        httpx.ReadTimeout("demorou demais")))
    r = infra["chamados"].patch(f"/chamados/{cid}/atribuir", headers=infra["contas"]["carla"]["headers"],
                                json={"tecnico_id": infra["contas"]["carla"]["id"]})
    assert r.status_code == 503 and "Usuários" in r.json()["detail"]
