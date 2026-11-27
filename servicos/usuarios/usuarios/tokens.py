"""Tokens JWT: o login cria; os demais serviços apenas validam com o mesmo segredo."""
from datetime import datetime, timedelta, timezone

import jwt

from usuarios.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO, TOKEN_MINUTOS


class TokenInvalido(Exception):
    pass


def criar(usuario_id: int, perfil: str) -> tuple[str, datetime]:
    agora = datetime.now(timezone.utc)
    expira = agora + timedelta(minutes=TOKEN_MINUTOS)
    dados = {"sub": str(usuario_id), "perfil": perfil, "iat": agora, "exp": expira, "iss": JWT_EMISSOR}
    return jwt.encode(dados, JWT_SEGREDO, algorithm=JWT_ALGORITMO), expira


def ler(token: str) -> dict:
    """Devolve {"id", "perfil"} do token, ou lança TokenInvalido."""
    try:
        dados = jwt.decode(
            token, JWT_SEGREDO, algorithms=[JWT_ALGORITMO], issuer=JWT_EMISSOR,
            options={"require": ["exp", "iat", "sub", "iss", "perfil"]},
        )
        return {"id": int(dados["sub"]), "perfil": dados["perfil"]}
    except (jwt.PyJWTError, ValueError, KeyError) as erro:
        raise TokenInvalido() from erro
