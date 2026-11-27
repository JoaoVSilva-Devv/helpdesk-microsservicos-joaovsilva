"""Validação local do JWT com o segredo compartilhado (sem ler banco de outro serviço)."""
from jwt import PyJWTError, decode

from chamados.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO


class TokenInvalido(Exception):
    pass


def ler(token: str) -> dict:
    try:
        dados = decode(
            token, JWT_SEGREDO, algorithms=[JWT_ALGORITMO], issuer=JWT_EMISSOR,
            options={"require": ["exp", "iat", "sub", "iss", "perfil"]},
        )
        return {"id": int(dados["sub"]), "perfil": dados["perfil"]}
    except (PyJWTError, ValueError, KeyError) as erro:
        raise TokenInvalido() from erro
