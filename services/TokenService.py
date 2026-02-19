import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from loguru import logger
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


class TokenService:
    def __init__(self, secret_key: str, algorithm: str, expire_minutes: int):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    # ---------- PASSWORD ----------
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.bind(service=self.__class__.__name___).exception(f"Error verifying password: {e}")
            return False

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    # ---------- ACCESS TOKEN ----------
    def create_access_token(self, data: dict, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.now(UTC) + expires_delta
        to_encode.update({"exp": int(expire.timestamp())})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    # ---------- REFRESH TOKEN ----------
    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(64)

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
