import datetime
import secrets
from typing import Any

import jwt

SECRET_KEY = "fc2b20edc79f41422c1cbaf115be91b9"
ALGORITHM = "HS256"


def create_jwt(
    payload: dict[str, Any], expires_delta: datetime.timedelta | None = None
) -> str:
    """Створення JWT з опціональним терміном дії."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    payload_copy = payload.copy()

    if expires_delta is not None:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + datetime.timedelta(minutes=15)

    jti = secrets.token_urlsafe()
    payload_copy.update(exp=expire, iat=now_utc, jti=jti)

    try:
        token = jwt.encode(payload_copy, key=SECRET_KEY, algorithm=ALGORITHM)
    except jwt.PyJWTError as e:
        raise ValueError(f"Error while encoding token: {e}") from e

    return token


def decode_jwt(encoded_token: bytes) -> dict[str, Any]:
    """Отримання вмісту токена (payload) після розкодування."""
    try:
        token = jwt.decode(
            encoded_token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except jwt.PyJWTError as e:
        raise ValueError(f"Error while decoding token: {e}") from e

    return token


if __name__ == "__main__":
    jwt_payload = {
        "sub": "example@example.com",
        "user_id": 123,
    }

    token = create_jwt(jwt_payload)
    print(token)
    decoded_token = decode_jwt(token.encode("utf-8"))
    print(decoded_token)
