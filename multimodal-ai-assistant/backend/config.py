import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
CHROMA_DIR = UPLOADS_DIR / "chroma_db"
DB_PATH = BACKEND_DIR / "app.db"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


def _first_non_empty(*keys: str, default: str = "") -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return default


def _normalize_openrouter_url(raw_url: str) -> str:
    default_url = "https://openrouter.ai/api/v1/chat/completions"
    url = (raw_url or "").strip().strip('"').strip("'")

    if not url:
        return default_url

    normalized = url.rstrip("/")

    if "openrouter.ai/openai/" in normalized:
        return default_url

    if normalized.endswith("/chat/completions"):
        return normalized

    if normalized.endswith("/api/v1"):
        return f"{normalized}/chat/completions"

    if normalized.startswith("https://openrouter.ai") and "/api/v1" not in normalized:
        return default_url

    return f"{normalized}/chat/completions"


def _parse_origins(origins_csv: str) -> list[str]:
    origins = [item.strip() for item in origins_csv.split(",") if item.strip()]
    return origins or ["http://localhost:8000", "http://127.0.0.1:8000"]


OPENROUTER_API_KEY = _first_non_empty("OPENROUTER_API_KEY", "OPENAI_API_KEY")
OPENROUTER_MODEL = _first_non_empty(
    "OPENROUTER_MODEL",
    "OPENAI_MODEL",
    default="openai/gpt-4o-mini",
)
OPENROUTER_URL = _normalize_openrouter_url(
    _first_non_empty("OPENROUTER_URL", "OPENROUTER_BASE_URL", "OPENAI_BASE_URL")
)

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)

MAX_UPLOAD_SIZE_BYTES = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".docx", ".csv", ".xlsx", ".pptx"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".csv", ".xlsx", ".pptx"}

SECRET_KEY = _first_non_empty(
    "APP_SECRET_KEY",
    "SECRET_KEY",
    default="change-this-secret-in-production",
)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "omni_auth_token")
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "strict")

FRONTEND_ORIGINS = _parse_origins(
    os.getenv("FRONTEND_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
)
