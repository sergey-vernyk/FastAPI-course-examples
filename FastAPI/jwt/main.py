from typing import Any

import bcrypt
import utils
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Security, security, status
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="JWT & Scopes")

oath2_schema = security.OAuth2PasswordBearer(
    "token",
    "bearer",
    scopes={"me": "Read information about the current user.", "items": "Read items."},
)


# pip install bcrypt pyjwt
class Token(BaseModel):
    """Модель токена доступу."""

    token_type: str
    access_token: str


class TokenData(BaseModel):
    """Модель для збереження `scope` для доступу до ресурсів."""

    email: EmailStr
    scopes: list[str] = Field(default_factory=list)


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


@app.post("/token", response_model=Token)
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

    token = utils.create_jwt({"sub": form_data.username, "scopes": form_data.scopes})
    return Token(access_token=token, token_type="bearer")


async def get_current_user(
    security_scopes: security.SecurityScopes, token: str = Depends(oath2_schema)
) -> dict[str, str]:
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

    token_data = TokenData(email=email, scopes=payload.get("scopes", []))

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions.",
                headers={
                    "WWW-Authenticate": f"Bearer scope={security_scopes.scope_str}",
                },
            )

    return fake_users_db[email]


@app.get("/me", status_code=status.HTTP_200_OK, response_model=None)
async def me_info(
    user: dict[str, Any] = Security(get_current_user, scopes=["me"]),
) -> dict[str, str]:
    """Ендпоінт захищений за допомогою JWT та `scope`."""
    if user["active"]:
        return user

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user."
    )


@app.get("/items", status_code=status.HTTP_200_OK, response_model=None)
async def get_items(
    user: dict[str, Any] = Security(get_current_user, scopes=["items"]),
) -> list[dict[str, Any]]:
    """Отримання об'єктів для поточного користувача."""
    return [
        {"item_id": 1, "owner": user["email"]},
        {"item_id": 2, "owner": user["email"]},
    ]


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
