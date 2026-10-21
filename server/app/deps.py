from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.errors import Unauthorized
from app.services.auth_service import AuthService, get_auth_service

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str | None
    token: str


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    auth: AuthService = Depends(get_auth_service),
) -> AuthUser:
    if creds is None or creds.scheme.lower() != "bearer":
        raise Unauthorized("missing bearer token")
    u = auth.get_user(creds.credentials)
    return AuthUser(id=u["id"], email=u.get("email"), token=creds.credentials)
