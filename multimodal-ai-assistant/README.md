# OmniModal AI Assistant

A production-ready multi-modal AI assistant built with FastAPI and a modern Bootstrap interface.

It supports:
- Text questions
- Image understanding
- Document Q&A and summarization (PDF, DOCX, CSV, XLSX, PPTX)
- Multi-modal reasoning across mixed inputs in one prompt

---

## 1) Client Overview

**OmniModal AI Assistant** is designed for teams that need one assistant for mixed content:
- Ask normal questions
- Upload one or more files
- Ask for summaries, key points, and cross-file reasoning
- Manage uploaded files in a secure, user-specific workspace

The interface is ChatGPT-style, responsive, and supports Light/Dark themes.

---

## 2) Core Features

- Secure user authentication (Register/Login/Logout)
- User-isolated file storage and file history
- File CRUD operations:
  - Upload
  - View/list
  - Rename
  - Delete
- Multi-modal chat with auto-context selection
- RAG pipeline for document understanding using embeddings + ChromaDB
- Drag-and-drop upload UX
- Markdown-formatted AI responses
- Theme persistence (Light/Dark mode saved in browser)

---

## 3) Supported File Types

### Images
- `.jpg`
- `.jpeg`
- `.png`

### Documents
- `.pdf`
- `.docx`
- `.csv`
- `.xlsx`
- `.pptx`

Upload limit: **15 MB per file**

---

## 4) Technology Stack

### Frontend
- HTML
- CSS
- Bootstrap 5
- Vanilla JavaScript

### Backend
- Python
- FastAPI

### AI + Retrieval
- OpenRouter API (`openai/gpt-4o-mini` by default)
- sentence-transformers (embeddings)
- ChromaDB (vector store)

### File Processing
- PyMuPDF (PDF)
- python-docx (DOCX)
- pandas + openpyxl (CSV/XLSX)
- python-pptx (PPTX)

### Database
- SQLite (file metadata + users)
- SQLAlchemy ORM

---

## 5) Project Structure

```text
multimodal-ai-assistant/
  backend/
    main.py
    config.py
    auth.py
    database.py
    llm_client.py
    embedding_engine.py
    vector_store.py
    fusion_engine.py
    models/
      file_model.py
      user_model.py
    processors/
      image_processor.py
      pdf_processor.py
      docx_processor.py
      csv_processor.py
      xlsx_processor.py
      pptx_processor.py
    routers/
      auth_router.py
      upload_router.py
      history_router.py
      chat_router.py
    requirements.txt
  frontend/
    index.html
    login.html
    register.html
    style.css
    auth.css
    script.js
    auth.js
  uploads/
  .env
  README.md
```

---

## 6) How the Assistant Works

### Text-only Chat
1. User sends question
2. Backend forwards prompt to OpenRouter
3. Response appears in chat bubble

### Image Understanding
1. Image uploaded
2. Image converted to base64
3. Vision call generates image description
4. Description is fused with user question

### Document RAG Pipeline
1. Document uploaded
2. Text extracted by processor
3. Text split into chunks
4. Chunks embedded with sentence-transformers
5. Embeddings stored in ChromaDB
6. On question, top relevant chunks are retrieved
7. Retrieved context + user question sent to LLM

### Multi-modal Fusion
If multiple files are selected, final prompt context combines:
- image descriptions
- retrieved document chunks
- user question

---

## 7) Security Design

- Password hashing with `passlib` (`pbkdf2_sha256`)
- JWT authentication in **HttpOnly cookie**
- Per-user file ownership checks for:
  - list files
  - open file
  - rename file
  - delete file
  - use file in chat
- File type whitelist validation
- Upload size limits
- Safe filename handling
- Environment-based secret configuration

---

## 8) API Endpoints

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### Files
- `POST /upload`
- `GET /files`
- `PUT /files/{id}`
- `DELETE /files/{id}`
- `GET /uploads/{filename}` (owner-protected)

### Chat
- `POST /chat`

---

## 9) Environment Variables

Create a `.env` in project root:

```env
# OpenRouter
OPENAI_API_KEY=your_openrouter_key
OPENAI_MODEL=openai/gpt-4o-mini
OPENAI_BASE_URL=https://openrouter.ai/api/v1/chat/completions

# App Security
APP_SECRET_KEY=change_this_to_a_long_random_secret
ACCESS_TOKEN_EXPIRE_MINUTES=1440
AUTH_COOKIE_NAME=omni_auth_token
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=strict

# Optional CORS origins
FRONTEND_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

Notes:
- `OPENROUTER_API_KEY` or `OPENAI_API_KEY` are both supported.
- Use `AUTH_COOKIE_SECURE=true` in production over HTTPS.

---

## 10) Run Locally

### Prerequisites
- Python 3.11+ recommended
- Node.js (optional, only used for JS syntax checks)

### Install

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Start Server

```bash
cd backend
uvicorn main:app --reload
```

Open:
- `http://localhost:8000/login`

---

## 11) Testing and Verification

Recommended checks:

```bash
# Backend syntax
python -m py_compile main.py auth.py routers\auth_router.py routers\chat_router.py routers\history_router.py routers\upload_router.py

# Frontend syntax (from project root)
node --check frontend\script.js
node --check frontend\auth.js
```

Functional checks:
- Register a new user
- Login/logout flow
- Upload each supported file type
- Rename/delete file
- Ask summarization and multi-file questions
- Verify dark/light mode in both auth and app screens

---

## 12) Production Notes

- Use HTTPS and set `AUTH_COOKIE_SECURE=true`
- Set a strong `APP_SECRET_KEY`
- Restrict `FRONTEND_ORIGINS`
- Add reverse proxy (Nginx/Caddy) and process manager (systemd/PM2/supervisor)
- Add monitoring and request logging

---

## 13) Business Use Cases

- Academic assistant for lecture notes and slides
- Operations assistant for CSV/XLSX reports
- Documentation assistant for PDFs and DOCX manuals
- Visual + document combined analysis workflows

