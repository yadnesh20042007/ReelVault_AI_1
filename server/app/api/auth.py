from fastapi import APIRouter, Depends, Response

from app.deps import AuthUser, current_user
from app.schemas.auth import LoginIn, LogoutIn, RefreshIn, SignupIn, SignupOut, TokenOut, UserOut
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_out(d: dict) -> TokenOut:
    u = d["user"]
    return TokenOut(
        access_token=d["access_token"],
        refresh_token=d["refresh_token"],
        expires_in=d["expires_in"],
        user=UserOut(id=u["id"], email=u.get("email")),
    )


@router.post("/signup", response_model=SignupOut, status_code=201)
def signup(body: SignupIn, auth: AuthService = Depends(get_auth_service)):
    r = auth.sign_up(body.email, body.password)
    return SignupOut(
        user=UserOut(id=r["user"]["id"], email=r["user"].get("email")),
        confirmation_required=r["confirmation_required"],
        session=_token_out(r["session"]) if r["session"] else None,
    )


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, auth: AuthService = Depends(get_auth_service)):
    return _token_out(auth.sign_in(body.email, body.password))


@router.post("/refresh", response_model=TokenOut)
def refresh(body: RefreshIn, auth: AuthService = Depends(get_auth_service)):
    return _token_out(auth.refresh(body.refresh_token))


@router.post("/logout", status_code=204)
def logout(
    body: LogoutIn | None = None,
    user: AuthUser = Depends(current_user),
    auth: AuthService = Depends(get_auth_service),
):
    auth.sign_out(user.token, all_devices=bool(body and body.all_devices))
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(user: AuthUser = Depends(current_user)):
    return UserOut(id=user.id, email=user.email)
