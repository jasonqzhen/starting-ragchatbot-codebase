# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval-Augmented Generation) chatbot for querying course materials. Uses ChromaDB for vector storage, Anthropic Claude for AI generation, and a vanilla JS frontend served by FastAPI.

## Commands

```bash
# Install dependencies (requires uv)
uv sync

# Run the app (starts FastAPI on port 8000)
./run.sh
# Or manually:
cd backend && uv run uvicorn app:app --reload --port 8000

# On Windows: use Git Bash for shell commands
```

No test suite or linter is configured.

## Architecture

**Request flow:** Frontend (`frontend/`) → FastAPI (`backend/app.py`) → `RAGSystem` → Claude API with tool use → response

**Backend components (all in `backend/`):**

- `rag_system.py` — Main orchestrator. Wires together all components and exposes `query()` and `add_course_folder()`.
- `document_processor.py` — Parses course `.txt` files (expected format: title/link/instructor header, then `Lesson N:` sections), chunks text with sentence-aware splitting.
- `vector_store.py` — ChromaDB wrapper with two collections: `course_catalog` (metadata/titles) and `course_content` (chunked text). Handles semantic course name resolution.
- `ai_generator.py` — Claude API client. Implements a tool-use loop: initial request → tool execution → follow-up response.
- `search_tools.py` — Tool abstraction layer. `CourseSearchTool` wraps `VectorStore.search()` as an Anthropic tool definition. `ToolManager` registers tools and dispatches calls.
- `session_manager.py` — In-memory conversation history, keyed by session ID.
- `models.py` — Pydantic models: `Course`, `Lesson`, `CourseChunk`.
- `config.py` — Dataclass config loaded from `.env`. Key settings: chunk size (800), overlap (100), max results (5), model (`claude-sonnet-4-20250514`).

**Frontend (`frontend/`):** Static HTML/CSS/JS served by FastAPI's `StaticFiles` mount at `/`. Uses `marked.js` for markdown rendering. Calls `/api/query` and `/api/courses`.

**Data:** Course documents live in `docs/` as `.txt` files and are auto-loaded on startup. ChromaDB persists to `backend/chroma_db/` (gitignored).

## Environment

- Python 3.13+, managed with `uv`
- Requires `ANTHROPIC_API_KEY` in `.env` (see `.env.example`)
