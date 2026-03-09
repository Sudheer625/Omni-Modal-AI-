from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from auth import get_current_user, is_token_valid
from config import AUTH_COOKIE_NAME, FRONTEND_DIR, FRONTEND_ORIGINS, UPLOADS_DIR
from database import get_db, init_db
from embedding_engine import EmbeddingEngine
from fusion_engine import FusionEngine
from llm_client import OpenRouterClient
from models.file_model import FileRecord
from models.user_model import UserRecord
from routers.auth_router import router as auth_router
from routers.chat_router import router as chat_router
from routers.history_router import router as history_router
from routers.upload_router import router as upload_router
from vector_store import VectorStore


app = FastAPI(title="OmniModal AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.state.llm_client = OpenRouterClient()
app.state.embedding_engine = EmbeddingEngine()
app.state.vector_store = VectorStore()
app.state.fusion_engine = FusionEngine(app.state.llm_client)

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(history_router)
app.include_router(chat_router)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def _is_authenticated(request: Request) -> bool:
    token = request.cookies.get(AUTH_COOKIE_NAME)
    return is_token_valid(token)


@app.get("/")
async def serve_frontend(request: Request):
    if not _is_authenticated(request):
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(Path(FRONTEND_DIR) / "index.html")


@app.get("/login")
async def serve_login(request: Request):
    if _is_authenticated(request):
        return RedirectResponse(url="/", status_code=302)
    return FileResponse(Path(FRONTEND_DIR) / "login.html")


@app.get("/register")
async def serve_register(request: Request):
    if _is_authenticated(request):
        return RedirectResponse(url="/", status_code=302)
    return FileResponse(Path(FRONTEND_DIR) / "register.html")


@app.get("/uploads/{filename}")
async def serve_upload(
    filename: str,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    safe_filename = Path(filename).name

    owned_paths = (
        db.query(FileRecord.filepath)
        .filter(FileRecord.owner_id == current_user.id)
        .all()
    )
    matching_path = next(
        (Path(item.filepath) for item in owned_paths if Path(item.filepath).name == safe_filename),
        None,
    )

    if not matching_path or not matching_path.exists() or not matching_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(matching_path)
