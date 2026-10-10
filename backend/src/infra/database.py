import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

env_path = Path(__file__).resolve().parents[2] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/deskflow"

if "@db:5432" in DATABASE_URL and not os.path.exists("/.dockerenv"):
    DATABASE_URL = DATABASE_URL.replace("@db:5432", "@localhost:5432")

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI dependency yielding an async SQLAlchemy session."""
    async with SessionLocal() as session:
        yield session
