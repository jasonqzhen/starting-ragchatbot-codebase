"""Shared pytest fixtures for backend tests.

The production FastAPI app in backend/app.py mounts a static directory
(`../frontend`) and performs heavy RAG initialization at import time.
Neither is desirable inside the test environment, so fixtures here build
a standalone FastAPI app that mirrors the real endpoints but wires in a
mocked RAGSystem.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel

# Ensure `backend/` is importable as a top-level package path when tests
# are invoked from the repo root.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_course_titles() -> List[str]:
    return [
        "Building Toward Computer Use with Anthropic",
        "MCP: Build Rich-Context AI Apps with Anthropic",
        "Advanced Retrieval for AI with Chroma",
    ]


@pytest.fixture
def sample_analytics(sample_course_titles):
    return {
        "total_courses": len(sample_course_titles),
        "course_titles": sample_course_titles,
    }


@pytest.fixture
def sample_query_answer():
    return (
        "Anthropic's computer use feature lets Claude control a desktop by "
        "taking screenshots and issuing mouse/keyboard actions.",
        ["Building Toward Computer Use with Anthropic - Lesson 2"],
    )


# ---------------------------------------------------------------------------
# Mocked RAG system
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_rag_system(sample_analytics, sample_query_answer):
    """A MagicMock that mimics the surface of RAGSystem used by the API."""
    rag = MagicMock()
    rag.session_manager = MagicMock()
    rag.session_manager.create_session.return_value = "test-session-id"
    rag.query.return_value = sample_query_answer
    rag.get_course_analytics.return_value = sample_analytics
    return rag


# ---------------------------------------------------------------------------
# Standalone test FastAPI app
# ---------------------------------------------------------------------------


class _QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class _QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str


class _CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


def _build_test_app(rag_system) -> FastAPI:
    """Build a minimal FastAPI app that mirrors backend/app.py endpoints.

    The real app mounts ``../frontend`` as static files, which doesn't exist
    in the test environment and would make ``TestClient`` raise on startup.
    This factory omits the static mount and takes an injected ``rag_system``
    so tests can assert against a mock.
    """
    app = FastAPI(title="Course Materials RAG System (test)")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/api/query", response_model=_QueryResponse)
    async def query_documents(request: _QueryRequest):
        try:
            session_id = request.session_id or rag_system.session_manager.create_session()
            answer, sources = rag_system.query(request.query, session_id)
            return _QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as exc:  # pragma: no cover - exercised via tests
            raise HTTPException(status_code=500, detail=str(exc))

    @app.get("/api/courses", response_model=_CourseStats)
    async def get_course_stats():
        try:
            analytics = rag_system.get_course_analytics()
            return _CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as exc:  # pragma: no cover - exercised via tests
            raise HTTPException(status_code=500, detail=str(exc))

    @app.get("/")
    async def root():
        return {"message": "Course Materials RAG System", "status": "ok"}

    return app


@pytest.fixture
def test_app(mock_rag_system) -> FastAPI:
    return _build_test_app(mock_rag_system)


@pytest.fixture
def client(test_app) -> TestClient:
    return TestClient(test_app)
