from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DB_PATH


DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def _ensure_files_owner_column() -> None:
    with engine.begin() as conn:
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info(files)"))]
        if "owner_id" not in columns:
            conn.execute(text("ALTER TABLE files ADD COLUMN owner_id INTEGER"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_files_owner_id ON files(owner_id)"))


def init_db() -> None:
    from models.file_model import FileRecord  # noqa: F401
    from models.user_model import UserRecord  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_files_owner_column()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
