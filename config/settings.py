import os

from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL")
HOME_URL = os.getenv("HOME_URL")
LOCAL_URL = os.getenv("LOCAL_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="token")
