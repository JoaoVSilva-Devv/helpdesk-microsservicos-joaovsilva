"""API Gateway do HelpDesk.

Único ponto exposto (porta 8000): serve a tela e encaminha /auth, /usuarios,
/ativos, /chamados e /notificacoes para os serviços correspondentes.
"""
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from gateway.config import DOCS_ATIVA, HTTP_TIMEOUT_SEGUNDOS, NOME_SERVICO, ROTAS, SERVICOS
from gateway.seguranca import CabecalhosDeSeguranca

WEB = Path(__file__).parent / "web"

# Cabeçalhos que não devem ser repassados de um lado para o outro.
IGNORAR = {
    "host", "content-length", "transfer-encoding", "connection", "keep-alive",
    "accept-encoding", "te", "trailer", "upgrade", "proxy-authenticate", "proxy-authorization",
}

app = FastAPI(
    title="HelpDesk TI · Gateway", version="1.0.0",
    docs_url="/docs" if DOCS_ATIVA else None, redoc_url=None,
    openapi_url="/openapi.json" if DOCS_ATIVA else None,
)
app.add_middleware(CabecalhosDeSeguranca)


def _servico_do_caminho(caminho: str) -> str | None:
    for prefixo, servico in ROTAS.items():
        if caminho == prefixo or caminho.startswith(prefixo + "/"):
            return servico
    return None


def _indisponivel(servico: str) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": f"Serviço de {NOME_SERVICO[servico]} indisponível. Tente novamente em instantes."},
    )


@app.get("/saude", tags=["Saúde"])
async def saude():
    """Painel de saúde: mostra quais serviços estão no ar."""
    estado = {}
    for nome, base in SERVICOS.items():
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SEGUNDOS) as cliente:
                resposta = await cliente.get(f"{base}/saude")
            estado[nome] = resposta.json() if resposta.status_code == 200 else {"status": "erro", "codigo": resposta.status_code}
        except (httpx.RequestError, httpx.TimeoutException):
            estado[nome] = {"status": "fora do ar"}
    return {"status": "ok" if all(v.get("status") == "ok" for v in estado.values()) else "degradado",
            "servicos": estado}


@app.get("/", include_in_schema=False)
def tela_inicial():
    return FileResponse(WEB / "index.html")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(WEB / "app.js", media_type="text/javascript")


@app.get("/estilo.css", include_in_schema=False)
def estilo():
    return FileResponse(WEB / "estilo.css", media_type="text/css")


@app.api_route("/{caminho:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
               include_in_schema=False)
async def encaminhar(caminho: str, request: Request):
    destino = _servico_do_caminho("/" + caminho)
    if destino is None:
        return JSONResponse(status_code=404, content={"detail": "Rota não encontrada."})

    url = f"{SERVICOS[destino]}/{caminho}"
    cabecalhos = {k: v for k, v in request.headers.items() if k.lower() not in IGNORAR}
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SEGUNDOS) as cliente:
            resposta = await cliente.request(
                request.method, url, params=request.query_params,
                content=await request.body(), headers=cabecalhos,
            )
    except (httpx.RequestError, httpx.TimeoutException):
        return _indisponivel(destino)

    resposta_cabecalhos = {
        k: v for k, v in resposta.headers.items()
        if k.lower() not in IGNORAR and k.lower() != "content-encoding"
    }
    return Response(content=resposta.content, status_code=resposta.status_code, headers=resposta_cabecalhos)
