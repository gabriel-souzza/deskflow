import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from infra.models import Base

env_path = Path(__file__).resolve().parents[3] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

config = context.config
fileConfig(config.config_file_name)

database_url = os.getenv("DATABASE_URL")
if not database_url:
    database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/deskflow"

if "@db:5432" in database_url and not os.path.exists("/.dockerenv"):
    database_url = database_url.replace("@db:5432", "@localhost:5432")

config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
