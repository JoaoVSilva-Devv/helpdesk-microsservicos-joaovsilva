"""Configurações do gateway."""
import os

# Maior que o timeout dos serviços: assim a mensagem de erro do serviço chega
# ao cliente antes do gateway desistir da requisição.
HTTP_TIMEOUT_SEGUNDOS = float(os.getenv("GATEWAY_TIMEOUT_SEGUNDOS", "5"))
TAMANHO_MAXIMO_REQUISICAO = 64 * 1024
DOCS_ATIVA = os.getenv("DOCS", "1") == "1"

# Os serviços são chamados pelo nome do serviço dentro da rede do Docker.
SERVICOS = {
    "usuarios": os.getenv("USUARIOS_URL", "http://usuarios:8000"),
    "inventario": os.getenv("INVENTARIO_URL", "http://inventario:8000"),
    "chamados": os.getenv("CHAMADOS_URL", "http://chamados:8000"),
}

# Prefixo da URL -> serviço de destino (notificações mora no serviço de chamados).
ROTAS = {
    "/auth": "usuarios",
    "/usuarios": "usuarios",
    "/ativos": "inventario",
    "/chamados": "chamados",
    "/notificacoes": "chamados",
}

NOME_SERVICO = {"usuarios": "Usuários", "inventario": "Inventário", "chamados": "Chamados"}
