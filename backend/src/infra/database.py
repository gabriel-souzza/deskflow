import os
import urllib.parse
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


def clean_postgres_url(raw_url: str | None) -> str:
    """Normaliza URLs de bancos gerenciados (Neon, Supabase, Render) para o driver asyncpg."""
    if not raw_url:
        return "postgresql+asyncpg://postgres:postgres@localhost:5432/deskflow"
    url = raw_url.strip()

    # Preserva sqlite e outros drivers de teste
    if url.startswith("sqlite"):
        return url

    # Normaliza esquema para asyncpg
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    elif not url.startswith("postgresql+asyncpg://") and url.startswith(("postgres", "pgsql")):
        scheme, rest = url.split("://", 1)
        url = f"postgresql+asyncpg://{rest}"

    # Ajusta hostname se estiver rodando localmente fora do docker
    if "@db:5432" in url and not os.path.exists("/.dockerenv"):
        url = url.replace("@db:5432", "@localhost:5432")

    parsed = urllib.parse.urlsplit(url)
    query_params = urllib.parse.parse_qs(parsed.query)

    # Converte sslmode (incompatível com asyncpg) para ssl=require e remove parâmetros desconhecidos
    clean_params: dict[str, str] = {}
    if "sslmode" in query_params:
        mode = query_params["sslmode"][0]
        if mode in ("require", "verify-ca", "verify-full", "prefer"):
            clean_params["ssl"] = "require"
    elif "ssl" in query_params:
        clean_params["ssl"] = query_params["ssl"][0]

    new_query = urllib.parse.urlencode(clean_params)
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment)
    )


DATABASE_URL = clean_postgres_url(os.getenv("DATABASE_URL"))

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI dependency yielding an async SQLAlchemy session."""
    async with SessionLocal() as session:
        yield session
