from datetime import datetime, timedelta, UTC
import jwt
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from config import settings

# Creates a password hasher
password_hash = PasswordHash.recommended()

# Defining the security scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/token")

# Hash a plain password
def hash_password(password: str) -> str:
    return password_hash.hash(password)

# Verify if password matches
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


# Create JWT access token
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({ "exp": expire })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm
    )

    return encoded_jwt

# Verify access token
def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]}
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")
