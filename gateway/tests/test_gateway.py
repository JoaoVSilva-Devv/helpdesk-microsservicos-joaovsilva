"""Testes do gateway: tela, encaminhamento e falha de um serviço."""
import httpx
from fastapi.testclient import TestClient

from gateway.main import app


class ClienteFalso:
    chamadas = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def request(self, metodo, url, **kwargs):
        self.chamadas.append((metodo, url, kwargs))
        return httpx.Response(201, json={"encaminhado": True}, headers={"content-type": "application/json"})

    async def get(self, url, **kwargs):
        return httpx.Response(200, json={"status": "ok"})


def test_tela_e_cabecalhos(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", ClienteFalso)
    with TestClient(app) as cliente:
        r = cliente.get("/")
        assert r.status_code == 200 and "HelpDesk" in r.text
        assert "script-src 'self'" in r.headers["content-security-policy"]
        assert r.headers["x-frame-options"] == "DENY"
        assert cliente.get("/app.js").status_code == 200
        assert cliente.get("/estilo.css").status_code == 200


def test_encaminha_mantendo_token(monkeypatch):
    ClienteFalso.chamadas.clear()
    monkeypatch.setattr(httpx, "AsyncClient", ClienteFalso)
    with TestClient(app) as cliente:
        r = cliente.post("/chamados", headers={"Authorization": "Bearer abc"},
                         params={"x": "1"}, json={"titulo": "Teste"})
        assert r.status_code == 201 and r.json() == {"encaminhado": True}
        metodo, url, kwargs = ClienteFalso.chamadas[0]
        assert metodo == "POST" and url == "http://chamados:8000/chamados"
        assert kwargs["headers"]["authorization"] == "Bearer abc"
        assert kwargs["params"]["x"] == "1"


def test_saude_agregada(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", ClienteFalso)
    with TestClient(app) as cliente:
        dados = cliente.get("/saude").json()
        assert dados["status"] == "ok"
        assert set(dados["servicos"]) == {"usuarios", "inventario", "chamados"}


def test_servico_fora_do_ar_responde_503(monkeypatch):
    class Quebrou(ClienteFalso):
        async def request(self, metodo, url, **kwargs):
            raise httpx.ConnectError("serviço fora do ar")

    monkeypatch.setattr(httpx, "AsyncClient", Quebrou)
    with TestClient(app) as cliente:
        r = cliente.get("/ativos")
        assert r.status_code == 503 and "Inventário" in r.json()["detail"]


def test_rota_desconhecida(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", ClienteFalso)
    with TestClient(app) as cliente:
        assert cliente.get("/nao-existe").status_code == 404
