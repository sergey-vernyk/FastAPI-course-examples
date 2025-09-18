import secrets
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from pydantic import BaseModel

app = FastAPI(title="dz ")

security_basic = HTTPBasic()

fake_users_db = {"john": "passwordDD7", "ann": "secret456863H"}


def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(security_basic)):
    user_password = fake_users_db.get(credentials.username)
    if user_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    if not secrets.compare_digest(credentials.password, user_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: Optional[str] = None


def fake_decode_token(token: str = Depends(oauth2_scheme)):
    user = User(username=token)
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# async def double_auth(request: Request):
#     # Basic Auth
#     basic_credentials: HTTPBasicCredentials = await security_basic(request)
#     if not (
#         basic_credentials.username in fake_users_db
#         and fake_users_db[basic_credentials.username] == basic_credentials.password
#     ):
#         raise HTTPException(status_code=401, detail="Basic auth failed")

#     # OAuth2
#     token = await oauth2_scheme(request)
#     user = await get_current_user(token)
#     if not user:
#         raise HTTPException(status_code=401, detail="OAuth2 failed")

#     return {"basic_user": basic_credentials.username, "oauth_user": user}


@app.get("/")
async def index():
    return {"message": "Welcome to the authentication demo:)!"}


@app.get("/auth/")
async def basic_auth_route(username: str = Depends(verify_basic_auth)):
    return {"message": f"Welcome, {username}!", "auth_type": "HTTP Basic"}


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_password = fake_users_db.get(form_data.username)
    if not user_password or not secrets.compare_digest(
        form_data.password, user_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = f"fake-token-{form_data.username}"

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected/")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Welcome to the secyre area, {current_user.username}!",
        "auth_type": "OAuth2",
    }


@app.get("/double-auth/")
async def double_auth_route(
    oauth_user: str = Security(get_current_user),
    basic_user: str = Depends(verify_basic_auth),
):
    return {
        "message": "Double authentication is successful :)",
        "oauth_user": oauth_user,
        "basic_user": basic_user,
    }


if __name__ == "__main__":
    uvicorn.run("hm11:app", host="127.0.0.1", port=8000, reload=True)
