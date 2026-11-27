"""Comunicação pela rede com Usuários e Inventário.

- usa httpx com timeout curto: um serviço fora do ar nunca trava os chamados;
- repassa o cabeçalho Authorization (token do usuário) em toda chamada;
- traduz falhas da rede para 503, com mensagem clara.
"""
import httpx
from fastapi import HTTPException, status

from chamados.config import HTTP_TIMEOUT_SEGUNDOS, INVENTARIO_URL, USUARIOS_URL
from chamados.erros import NaoEncontrado, RegraDeNegocio


def _get(url: str, token: str) -> httpx.Response:
    """Ponto único de saída HTTP (facilita testar e trocar o cliente)."""
    with httpx.Client(timeout=HTTP_TIMEOUT_SEGUNDOS) as cliente:
        return cliente.get(url, headers={"Authorization": token})


def _indisponivel(servico: str, erro: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Serviço de {servico} indisponível (tempo limite ou falha de conexão). Tente novamente.",
    )


def _traduzir_resposta(resposta: httpx.Response, servico: str, recurso: str) -> None:
    if resposta.status_code == 401:
        raise HTTPException(status_code=401, detail="Sua sessão expirou. Faça login novamente.",
                            headers={"WWW-Authenticate": "Bearer"})
    if resposta.status_code == 403:
        raise HTTPException(status_code=403, detail="Você não tem permissão para esta ação.")
    if resposta.status_code == 404:
        raise NaoEncontrado(f"{recurso} não encontrado.")
    if not 200 <= resposta.status_code < 300:
        raise _indisponivel(servico, None)


def obter_ativo(ativo_id: int, token: str) -> None:
    """Confere o equipamento no serviço de Inventário antes de abrir o chamado."""
    url = f"{INVENTARIO_URL}/ativos/{ativo_id}"
    try:
        resposta = _get(url, token)
    except (httpx.TimeoutException, httpx.RequestError) as erro:
        raise _indisponivel("Inventário", erro) from erro
    _traduzir_resposta(resposta, "Inventário", f"Ativo {ativo_id}")


def obter_tecnico(tecnico_id: int, token: str) -> dict:
    """Confere o técnico no serviço de Usuários antes de atribuir o chamado."""
    url = f"{USUARIOS_URL}/usuarios/{tecnico_id}"
    try:
        resposta = _get(url, token)
    except (httpx.TimeoutException, httpx.RequestError) as erro:
        raise _indisponivel("Usuários", erro) from erro
    _traduzir_resposta(resposta, "Usuários", f"Usuário {tecnico_id}")
    dados = resposta.json()
    if dados.get("perfil") != "tecnico":
        raise RegraDeNegocio(f"Usuário {tecnico_id} não é técnico.")
    return dados
