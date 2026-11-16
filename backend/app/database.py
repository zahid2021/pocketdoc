import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_DIR / 'pocketdoc.db'}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def ensure_columns():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        if "users" in tables:
            names = {column["name"] for column in inspector.get_columns("users")}
            if "area_district" not in names:
                conn.execute(text("ALTER TABLE users ADD COLUMN area_district VARCHAR DEFAULT ''"))
            if "area_division" not in names:
                conn.execute(text("ALTER TABLE users ADD COLUMN area_division VARCHAR DEFAULT ''"))
            if "password_plain" not in names:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_plain VARCHAR DEFAULT ''"))
            if "removed" not in names:
                conn.execute(text("ALTER TABLE users ADD COLUMN removed BOOLEAN DEFAULT 0"))
        if "clinics" in tables:
            names = {column["name"] for column in inspector.get_columns("clinics")}
            if "district" not in names:
                conn.execute(text("ALTER TABLE clinics ADD COLUMN district VARCHAR DEFAULT ''"))
            if "division" not in names:
                conn.execute(text("ALTER TABLE clinics ADD COLUMN division VARCHAR DEFAULT ''"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
