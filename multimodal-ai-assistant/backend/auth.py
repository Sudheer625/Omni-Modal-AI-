import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session

from config import ACCESS_TOKEN_EXPIRE_MINUTES, AUTH_COOKIE_NAME, SECRET_KEY
from database import get_db
from models.user_model import UserRecord


ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


class AuthError(Exception):
    pass


def validate_password_strength(password: str) -> None:
    checks = [
        (len(password) >= 8, "Password must be at least 8 characters long."),
        (re.search(r"[A-Z]", password) is not None, "Password must include at least one uppercase letter."),
        (re.search(r"[a-z]", password) is not None, "Password must include at least one lowercase letter."),
        (re.search(r"\d", password) is not None, "Password must include at least one number."),
        (
            re.search(r"[^A-Za-z0-9]", password) is not None,
            "Password must include at least one special character.",
        ),
    ]

    for passed, message in checks:
        if not passed:
            raise AuthError(message)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except (UnknownHashError, ValueError):
        return False


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        return str(subject) if subject is not None else None
    except JWTError:
        return None


def is_token_valid(token: Optional[str]) -> bool:
    if not token:
        return False
    return decode_access_token(token) is not None


def get_current_user(
    token: Optional[str] = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> UserRecord:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    subject = decode_access_token(token)
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    user = db.query(UserRecord).filter(UserRecord.id == user_id, UserRecord.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")

    return user
