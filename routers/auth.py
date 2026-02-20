from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_throttle import RateLimiter
from sqlalchemy.orm import Session

from db.DB import get_db
from dependencies import ACCESS_TOKEN_EXPIRE_MINUTES, token_service
from domain.models import (
    AccessToken,
    RefreshTokenDB,
    Token,
    UserCreate,
    UserDB,
    UserOut,
)
from services.UserService import UserService, get_user_service

auth_limit = RateLimiter(times=5, seconds=60)
router = APIRouter(prefix="/api/v1/auth", dependencies=[Depends(auth_limit)])


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    service = UserService(db)
    user = service.get_user(form_data.username)

    if not user or not token_service.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = token_service.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = token_service.create_refresh_token()
    refresh_token_hash = token_service.hash_refresh_token(refresh_token)

    refresh_db = RefreshTokenDB(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(refresh_db)
    db.commit()

    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh", response_model=AccessToken)
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    token_hash = token_service.hash_refresh_token(refresh_token)
    token_entry = (
        db.query(RefreshTokenDB)
        .filter(
            RefreshTokenDB.token_hash == token_hash, RefreshTokenDB.is_revoked == False
        )
        .first()
    )

    if not token_entry or token_entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(UserDB).filter(UserDB.id == token_entry.user_id).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = token_service.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return AccessToken(access_token=access_token)


@router.post("/logout")
def logout(refresh_token: str, db: Session = Depends(get_db)):
    token_hash = token_service.hash_refresh_token(refresh_token)
    token_entry = (
        db.query(RefreshTokenDB)
        .filter(
            RefreshTokenDB.token_hash == token_hash, RefreshTokenDB.is_revoked == False
        )
        .first()
    )

    if not token_entry:
        raise HTTPException(status_code=400, detail="Invalid token")

    token_entry.is_revoked = True
    db.commit()
    return {"message": "Logged out"}


@router.post("/register", response_model=UserOut)
def register_user(
    user_create: UserCreate,
    service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
):
    if service.get_user(user_create.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = token_service.hash_password(user_create.password)
    user_db = UserDB(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(UTC),
    )
    created_user = service.create_user(user_db)
    return created_user
