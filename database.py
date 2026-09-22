import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

db_URL = os.getenv("DATABASE_URL")
if db_URL is None:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(db_URL)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db