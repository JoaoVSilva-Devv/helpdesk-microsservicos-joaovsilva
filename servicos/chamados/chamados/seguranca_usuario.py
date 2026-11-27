"""Dependências de autenticação: token conferido antes de responder."""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from chamados import tokens

esquema = HTTPBearer(auto_error=False)

NAO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Faça login para continuar.",
    headers={"WWW-Authenticate": "Bearer"},
)


@dataclass(frozen=True)
class UsuarioToken:
    id: int
    perfil: str
    token: str  # "Bearer ..." — repassado nas chamadas HTTP aos outros serviços


def usuario_atual(credenciais: HTTPAuthorizationCredentials | None = Depends(esquema)) -> UsuarioToken:
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise NAO_AUTENTICADO
    try:
        claims = tokens.ler(credenciais.credentials)
    except tokens.TokenInvalido:
        raise NAO_AUTENTICADO
    return UsuarioToken(id=claims["id"], perfil=claims["perfil"], token=f"Bearer {credenciais.credentials}")


def exigir_perfil(*perfis: str):
    def verificar(usuario: UsuarioToken = Depends(usuario_atual)) -> UsuarioToken:
        if usuario.perfil not in perfis:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para esta ação.")
        return usuario
    return verificar
