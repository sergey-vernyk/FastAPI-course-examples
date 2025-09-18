from typing import Any

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, Request, security, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from FastAPI.jwt import utils

app = FastAPI()
templates = Jinja2Templates(directory="templates")
oath2_schema = security.OAuth2PasswordBearer(
    "token",
    "bearer",
)

fake_users_db = {
    "johndoe@example.com": {
        "full_name": "John Doe",
        "username": "johndoe",
        "hashed_password": "$2a$12$WiMBf1FGUjP0FVMB9p/nb.sXMlvtOH/MOYuE2K18x63IgkOwAI/Ga",  # john_password
        "active": True,
    },
    "marrysmith@example.com": {
        "full_name": "John Doe",
        "username": "marrysmith",
        "hashed_password": "$2a$12$7sDork7cD7aFIjZTWAwARetaYMGohDe6.LVuw/knsEqqH0N7XUgkK",  # marry_password
        "active": False,
    },
}


class Token(BaseModel):
    """Модель токена доступу."""

    token_type: str
    access_token: str


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/me-page", response_class=HTMLResponse)
async def me_page(request: Request):
    return templates.TemplateResponse("me.html", {"request": request})


@app.get("/items-page", response_class=HTMLResponse)
async def items_page(request: Request):
    return templates.TemplateResponse("items.html", {"request": request})


@app.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login(form_data: security.OAuth2PasswordRequestForm = Depends()) -> Token:
    """Отримання токену автентифікації для доступу до захищених ендпоінтів."""
    db_user = fake_users_db.get(form_data.username)

    if db_user is None or not bcrypt.checkpw(
        form_data.password.encode("utf-8"),
        db_user["hashed_password"].encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raw_token = utils.create_jwt({"sub": form_data.username})
    token = Token(access_token=raw_token, token_type="bearer")
    return token


async def get_current_user(token: str = Depends(oath2_schema)) -> dict[str, str]:
    """Отримання поточного користувача з переданого JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = utils.decode_jwt(token.encode("utf-8"))
    except ValueError as e:
        raise credentials_exception from e

    email = payload.get("sub")
    if email is None:
        raise credentials_exception

    return fake_users_db[email]


@app.get("/me", status_code=status.HTTP_200_OK, response_model=None)
async def me_info(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    """Ендпоінт захищений за допомогою JWT."""
    if user["active"]:
        return user

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user."
    )


@app.get("/items")
async def get_items(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"items": ["apple", "banana", "cherry"], "user": user}
