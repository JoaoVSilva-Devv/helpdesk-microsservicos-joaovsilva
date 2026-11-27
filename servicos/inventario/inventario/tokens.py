"""Validação local do JWT: o mesmo segredo do serviço de Usuários, sem ler o banco dele."""
from jwt import PyJWTError, decode

from inventario.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO


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
