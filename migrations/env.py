import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from database.database import Base

# Import models so SQLAlchemy registers them in Base.metadata
from database.models.user_model import User
from database.models.game_session_model import GameSession
from database.models.steam_tracking_state_model import SteamTrackingState

load_dotenv()

config = context.config

# --------------------------------------------------
# Database URL
# --------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )

config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL,
)

# --------------------------------------------------
# Logging
# --------------------------------------------------

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --------------------------------------------------
# SQLAlchemy metadata for Alembic autogenerate
# --------------------------------------------------

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()