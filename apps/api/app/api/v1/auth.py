from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.common import Message
from app.schemas.user import TokenPair, UserCreate, UserLogin, UserRead
from app.services import auth_service

router = APIRouter()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def register(
    request: Request, response: Response, payload: UserCreate, db: Session = Depends(get_db)
) -> TokenPair:
    user = auth_service.register_user(db, payload)
    access_token, refresh_token = auth_service.issue_tokens(db, user)
    _set_refresh_cookie(response, refresh_token)
    return TokenPair(access_token=access_token, user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenPair)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(
    request: Request, response: Response, payload: UserLogin, db: Session = Depends(get_db)
) -> TokenPair:
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    access_token, refresh_token = auth_service.issue_tokens(db, user)
    _set_refresh_cookie(response, refresh_token)
    return TokenPair(access_token=access_token, user=UserRead.model_validate(user))


@router.post("/refresh", response_model=TokenPair)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> TokenPair:
    raw_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )

    access_token, new_refresh_token, user = auth_service.rotate_refresh_token(db, raw_token)
    _set_refresh_cookie(response, new_refresh_token)
    return TokenPair(access_token=access_token, user=UserRead.model_validate(user))


@router.post("/logout", response_model=Message)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> Message:
    raw_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if raw_token:
        auth_service.revoke_refresh_token(db, raw_token)
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path="/")
    return Message(message="Logged out")
