from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from loguru import logger
from sqlalchemy.orm import Session

from config.settings import ALGORITHM, OAUTH2_SCHEME, SECRET_KEY
from db.DB import get_db
from domain.models import UserDB


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: UserDB) -> UserDB:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, username: str) -> UserDB | None:
        return self.db.query(UserDB).filter(UserDB.username == username).first()


# --- Factory para inyección ---
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


async def is_valid_request(
    token: str = Depends(OAUTH2_SCHEME),
    service: UserService = Depends(get_user_service),
) -> UserDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as exc:
        logger.bind(service="UserService").exception(f"JWT decode error: {exc}")
        raise credentials_exception from exc

    user = service.get_user(username)
    if user is None or not user.is_active:
        logger.bind(service="UserService").exception(f"JWT decode error: {exc}")
        raise credentials_exception

    return user
