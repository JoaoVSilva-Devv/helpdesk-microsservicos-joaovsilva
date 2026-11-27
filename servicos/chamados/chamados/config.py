"""Configurações do serviço de chamados (vêm do ambiente)."""
import logging
import os
import secrets

log = logging.getLogger("helpdesk-chamados")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chamados.db")

# Endereços dos outros serviços dentro da rede do Docker Compose.
USUARIOS_URL = os.getenv("USUARIOS_URL", "http://localhost:8001").rstrip("/")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://localhost:8002").rstrip("/")
HTTP_TIMEOUT_SEGUNDOS = float(os.getenv("HTTP_TIMEOUT_SEGUNDOS", "2"))

JWT_SEGREDO = os.getenv("JWT_SEGREDO") or ""
if len(JWT_SEGREDO) < 32:
    if JWT_SEGREDO:
        log.warning("JWT_SEGREDO com menos de 32 caracteres; gerando um segredo aleatório.")
    JWT_SEGREDO = secrets.token_urlsafe(48)

JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"
TAMANHO_MAXIMO_REQUISICAO = 64 * 1024
DOCS_ATIVA = os.getenv("DOCS", "1") == "1"
