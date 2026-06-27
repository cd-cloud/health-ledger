from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

from app.config import DATABASE_URL
from app.database import Base
from app import models  # noqa: F401  确保模型元数据被注册

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 使用与 FastAPI 应用一致的数据库 URL。
# 若调用方已通过 Config.set_main_option 指定 URL（如测试），则保持该值不变。
_DEFAULT_PLACEHOLDER = "driver://user:pass@localhost/dbname"
_current_url = config.get_main_option("sqlalchemy.url")
if not _current_url or _current_url == _DEFAULT_PLACEHOLDER:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


# SQLite 需要关闭同线程检查；对于 SQLite 尽量使用 batch 模式以支持后续 ALTER
_is_sqlite = DATABASE_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=_is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(
        url,
        connect_args=_connect_args,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=_is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
