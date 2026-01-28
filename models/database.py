from pathlib import Path
import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, DeclarativeBase

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "gallery.db"
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DEFAULT_DB_PATH}"
DB_URL = make_url(DATABASE_URL)
IS_SQLITE = DB_URL.drivername.startswith("sqlite")


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

def init_db() -> None:
    Base.metadata.create_all(engine)


def ensure_media_rating_columns() -> None:
    if not IS_SQLITE:
        return
    db_path = Path(DB_URL.database) if DB_URL.database else DEFAULT_DB_PATH
    if not db_path.exists():
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(media)")
        columns = {row[1] for row in cursor.fetchall()}

        if "rating" not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN rating INTEGER")
        if "rating_caption" not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN rating_caption TEXT")
        if "rated_at" not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN rated_at DATETIME")

        conn.commit()


def _normalize_model_key(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").split())


def ensure_model_normalized_columns() -> None:
    if not IS_SQLITE:
        return
    db_path = Path(DB_URL.database) if DB_URL.database else DEFAULT_DB_PATH
    if not db_path.exists():
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='models'")
        if cursor.fetchone() is None:
            return
        cursor.execute("PRAGMA table_info(models)")
        columns = {row[1] for row in cursor.fetchall()}

        if "normalized_name" not in columns:
            cursor.execute("ALTER TABLE models ADD COLUMN normalized_name TEXT")

        cursor.execute("SELECT id, name, normalized_name FROM models")
        rows = cursor.fetchall()

        canonical_by_norm: dict[str, int] = {}
        duplicates: list[int] = []

        for model_id, name, _ in rows:
            normalized = _normalize_model_key(name or "")
            if normalized in canonical_by_norm:
                duplicates.append(model_id)
            else:
                canonical_by_norm[normalized] = model_id

        for normalized, canonical_id in canonical_by_norm.items():
            cursor.execute(
                "UPDATE models SET normalized_name = ? WHERE id = ?",
                (normalized, canonical_id),
            )

        for dup_id in duplicates:
            cursor.execute(
                "SELECT name FROM models WHERE id = ?",
                (dup_id,),
            )
            dup_row = cursor.fetchone()
            normalized = _normalize_model_key(dup_row[0]) if dup_row else ""
            canonical_id = canonical_by_norm.get(normalized)
            if canonical_id is None:
                continue

            cursor.execute(
                "UPDATE media SET model_id = ? WHERE model_id = ?",
                (canonical_id, dup_id),
            )
            cursor.execute("DELETE FROM models WHERE id = ?", (dup_id,))

        cursor.execute(
            "UPDATE models SET normalized_name = ? WHERE normalized_name IS NULL",
            ("",),
        )

        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_models_normalized_name ON models(normalized_name)"
        )

        conn.commit()


def ensure_model_card_columns() -> None:
    if not IS_SQLITE:
        return
    db_path = Path(DB_URL.database) if DB_URL.database else DEFAULT_DB_PATH
    if not db_path.exists():
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='models'")
        if cursor.fetchone() is None:
            return
        cursor.execute("PRAGMA table_info(models)")
        columns = {row[1] for row in cursor.fetchall()}

        if "popularity" not in columns:
            cursor.execute("ALTER TABLE models ADD COLUMN popularity INTEGER")
        if "versatility" not in columns:
            cursor.execute("ALTER TABLE models ADD COLUMN versatility INTEGER")
        if "longevity" not in columns:
            cursor.execute("ALTER TABLE models ADD COLUMN longevity INTEGER")
        if "industry_impact" not in columns:
            cursor.execute("ALTER TABLE models ADD COLUMN industry_impact INTEGER")
        if "fan_appeal" not in columns:
            cursor.execute("ALTER TABLE models ADD COLUMN fan_appeal INTEGER")

        conn.commit()
