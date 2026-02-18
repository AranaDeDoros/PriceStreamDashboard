from logging import config

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

import config.settings

DATABASE_URL = config.settings.DATABASE_URL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
