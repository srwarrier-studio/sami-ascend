from auth_api.infrastructure.api.schema import UserInDB
from auth_api.application.dto.get_user_dto import GetUserDTO
from auth_api.infrastructure.mock.mock_unit_of_work import MockAuthUnitOfWork
from auth_api.application.usecase.get_user_by_email import GetUserByEmail
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
import uvicorn
from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from auth_api.infrastructure.interface.msal_auth_provider import MSALAuthProvider

auth_provider = MSALAuthProvider()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
app.add_middleware(SessionMiddleware, secret_key="your_super_secret_key")

router_head = APIRouter()

uow = MockAuthUnitOfWork()

def fake_hash_password(password: str):
    return "fakehashed" + password

@router_head.post("/token")
async def token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    usecase = GetUserByEmail(uow=uow)
    user_dict = usecase.execute(GetUserDTO(email_id=form_data.username))
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.userid, "token_type": "bearer"}

@router_head.get("/login")
async def login(request: Request):
    flow = auth_provider.initiate_flow()
    request.session["msal_flow"] = flow
    return RedirectResponse(url=flow["auth_uri"])

@router_head.get("/callback")
async def auth_callback(request: Request):
    flow = request.session.get("msal_flow")
    if not flow:
        return {"error": "Authentication flow not found. Please log in again."}
    
    auth_response = dict(request.query_params)
    result = auth_provider.authenticate(flow=flow, auth_response=auth_response)
    
    if "error" in result:
        return result
        
    request.session.pop("msal_flow", None)
    request.session["user"] = result.get("user")
    return result

app.include_router(router_head, prefix="/v1/auth", tags=["Auth"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)