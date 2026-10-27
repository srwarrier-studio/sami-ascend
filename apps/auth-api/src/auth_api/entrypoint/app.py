from typing import Annotated

import uvicorn
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from auth_api.application.dto.login_dto import LoginWithEntraDTO, LoginWithPasswordDTO
from auth_api.application.usecase.login_with_entra import LoginWithEntra
from auth_api.application.usecase.login_with_password import LoginWithPassword
from auth_api.core.config import settings
from auth_api.domain.errors import InvalidCredentials
from auth_api.infrastructure.interface.argon2_password_hasher import Argon2PasswordHasher
from auth_api.domain.value_objects.token_claims import TokenClaims
from auth_api.entrypoint.dependencies import ACCESS_TOKEN_COOKIE, current_claims, token_service
from auth_api.infrastructure.api.schema import Me
from auth_api.infrastructure.interface.msal_auth_provider import MSALAuthProvider
from auth_api.infrastructure.mock.mock_unit_of_work import MockAuthUnitOfWork

auth_provider = MSALAuthProvider()
uow = MockAuthUnitOfWork()
password_hasher = Argon2PasswordHasher()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

router_head = APIRouter()


def set_access_token_cookie(response: Response, token: str):
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=True,
        samesite="lax",
    )


@router_head.post("/login/password")
def login_with_password(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
):
    usecase = LoginWithPassword(uow, password_hasher, token_service)
    try:
        token = usecase.execute(
            LoginWithPasswordDTO(email_id=form_data.username, password=form_data.password)
        )
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    set_access_token_cookie(response, token)
    return {"message": "Logged in"}


@router_head.get("/login/entra")
def login_with_entra(request: Request):
    flow = auth_provider.initiate_flow()
    request.session["msal_flow"] = flow
    return RedirectResponse(url=flow["auth_uri"])


@router_head.get("/callback")
def entra_callback(request: Request):
    login_failed = RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=entra")

    flow = request.session.pop("msal_flow", None)
    if not flow:
        return login_failed

    result = auth_provider.authenticate(flow=flow, auth_response=dict(request.query_params))
    if "error" in result:
        return login_failed

    usecase = LoginWithEntra(uow, token_service)
    try:
        token = usecase.execute(LoginWithEntraDTO(email_id=result["user"]["email"] or ""))
    except InvalidCredentials:
        return login_failed

    response = RedirectResponse(url=settings.FRONTEND_URL)
    set_access_token_cookie(response, token)
    return response


@router_head.get("/me")
def me(claims: Annotated[TokenClaims, Depends(current_claims)]) -> Me:
    return Me(
        userid=claims.userid,
        sap_username=claims.sap_username,
        roles=[role.value for role in claims.roles],
    )


@router_head.post("/logout")
def logout(response: Response):
    response.delete_cookie(ACCESS_TOKEN_COOKIE)
    return {"message": "Logged out"}


app.include_router(router_head, prefix="/v1/auth", tags=["Auth"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
