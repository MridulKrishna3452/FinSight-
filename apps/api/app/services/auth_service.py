import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.schemas.user import UserCreate


def register_user(db: Session, payload: UserCreate) -> User:
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
    )
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise invalid_credentials
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(str(user.id))
    refresh_token = generate_refresh_token()

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=refresh_token_expiry(),
        )
    )
    db.commit()
    return access_token, refresh_token


def rotate_refresh_token(db: Session, raw_refresh_token: str) -> tuple[str, str, User]:
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )
    token_hash = hash_refresh_token(raw_refresh_token)

    stored = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()
    if stored is None or stored.revoked:
        raise invalid
    if stored.expires_at < datetime.now(UTC):
        raise invalid

    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise invalid

    # Rotate: revoke the used token and issue a new pair.
    stored.revoked = True
    db.commit()

    access_token, new_refresh_token = issue_tokens(db, user)
    return access_token, new_refresh_token, user


def revoke_refresh_token(db: Session, raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)
    stored = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()
    if stored is not None:
        stored.revoked = True
        db.commit()


def revoke_all_for_user(db: Session, user_id: uuid.UUID) -> None:
    tokens = db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id)).scalars().all()
    for token in tokens:
        token.revoked = True
    db.commit()
