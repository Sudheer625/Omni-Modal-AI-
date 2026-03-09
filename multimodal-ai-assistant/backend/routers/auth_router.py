from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import (
    AuthError,
    create_access_token,
    get_current_user,
    hash_password,
    validate_password_strength,
    verify_password,
)
from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AUTH_COOKIE_NAME,
    AUTH_COOKIE_SAMESITE,
    AUTH_COOKIE_SECURE,
)
from database import get_db
from models.user_model import LoginRequest, RegisterRequest, UserPublic, UserRecord


router = APIRouter(tags=["auth"])


def _normalize_username(username: str) -> str:
    clean = username.strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Username is required.")

    if len(clean) < 3 or len(clean) > 32:
        raise HTTPException(status_code=400, detail="Username must be between 3 and 32 characters.")

    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if any(char not in allowed for char in clean):
        raise HTTPException(
            status_code=400,
            detail="Username may contain letters, numbers, dots, underscores, and hyphens only.",
        )

    return clean


@router.post("/auth/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    username = _normalize_username(payload.username)
    email = payload.email.lower().strip()

    try:
        validate_password_strength(payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    existing = (
        db.query(UserRecord)
        .filter(
            (func.lower(UserRecord.username) == username.lower()) | (func.lower(UserRecord.email) == email)
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already exists.")

    user = UserRecord(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Registration successful.", "user": UserPublic.model_validate(user).model_dump()}


@router.post("/auth/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    identifier = payload.identifier.strip()
    if not identifier or not payload.password:
        raise HTTPException(status_code=400, detail="Identifier and password are required.")

    lowered = identifier.lower()
    user = (
        db.query(UserRecord)
        .filter((func.lower(UserRecord.email) == lowered) | (func.lower(UserRecord.username) == lowered))
        .first()
    )

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")

    token = create_access_token(str(user.id))
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
        max_age=int(timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds()),
        path="/",
    )

    return {"message": "Login successful.", "user": UserPublic.model_validate(user).model_dump()}


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    return {"message": "Logged out successfully."}


@router.get("/auth/me")
def me(current_user: UserRecord = Depends(get_current_user)):
    return UserPublic.model_validate(current_user).model_dump()
