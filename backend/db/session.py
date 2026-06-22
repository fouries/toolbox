from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings

settings = get_settings()


def _connect_args(database_url: str) -> dict:
    return {"check_same_thread": False} if database_url.startswith("sqlite") else {}


def _normalize_sqlite_path(database_url: str) -> str:
    if not database_url.startswith("sqlite"):
        return database_url
    prefix = "sqlite:///"
    raw_path = database_url[len(prefix):] if database_url.startswith(prefix) else ""
    if raw_path and not raw_path.startswith(('/', ':')):
        data_path = Path(__file__).resolve().parents[1] / raw_path
        data_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{data_path}"
    return database_url


DATABASE_URL = _normalize_sqlite_path(settings.DATABASE_URL)
engine = create_engine(
    DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    pool_pre_ping=True,
    connect_args=_connect_args(DATABASE_URL),
)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    pass


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _ensure_column(table_name: str, column_name: str, ddl: str) -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in columns:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def _run_lightweight_migrations() -> None:
    # SQLite create_all 不会给已有表补新增列；这里做轻量向前兼容迁移。
    _ensure_column("users", "wx_openid", "wx_openid VARCHAR(128) NOT NULL DEFAULT ''")
    _ensure_column("user_reminder_subscriptions", "wx_template_id", "wx_template_id VARCHAR(128) NOT NULL DEFAULT ''")
    _ensure_column("user_reminder_subscriptions", "wx_subscribe_enabled", "wx_subscribe_enabled BOOLEAN NOT NULL DEFAULT 0")
    _ensure_column("user_reminder_subscriptions", "last_sent_date", "last_sent_date VARCHAR(10) NOT NULL DEFAULT ''")


def init_db() -> None:
    from db import models  # noqa: F401 - register models

    Base.metadata.create_all(bind=engine)
    _run_lightweight_migrations()
