"""API endpoint tests for the RAG system FastAPI app.

These tests target the standalone test app built in ``conftest.py`` so they
don't trigger the real static file mount or heavy RAGSystem initialization.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# POST /api/query
# ---------------------------------------------------------------------------


class TestQueryEndpoint:
    def test_query_creates_session_when_missing(self, client, mock_rag_system, sample_query_answer):
        response = client.post("/api/query", json={"query": "What is computer use?"})

        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == sample_query_answer[0]
        assert body["sources"] == sample_query_answer[1]
        assert body["session_id"] == "test-session-id"

        mock_rag_system.session_manager.create_session.assert_called_once()
        mock_rag_system.query.assert_called_once_with(
            "What is computer use?", "test-session-id"
        )

    def test_query_reuses_provided_session(self, client, mock_rag_system):
        response = client.post(
            "/api/query",
            json={"query": "Tell me more", "session_id": "existing-session"},
        )

        assert response.status_code == 200
        assert response.json()["session_id"] == "existing-session"

        mock_rag_system.session_manager.create_session.assert_not_called()
        mock_rag_system.query.assert_called_once_with("Tell me more", "existing-session")

    def test_query_missing_field_returns_422(self, client):
        response = client.post("/api/query", json={})
        assert response.status_code == 422

    def test_query_wrong_type_returns_422(self, client):
        response = client.post("/api/query", json={"query": 123})
        assert response.status_code == 422

    def test_query_rag_error_returns_500(self, client, mock_rag_system):
        mock_rag_system.query.side_effect = RuntimeError("vector store offline")

        response = client.post("/api/query", json={"query": "anything"})

        assert response.status_code == 500
        assert "vector store offline" in response.json()["detail"]

    def test_query_response_schema(self, client):
        response = client.post("/api/query", json={"query": "hi"})
        body = response.json()
        assert set(body.keys()) == {"answer", "sources", "session_id"}
        assert isinstance(body["answer"], str)
        assert isinstance(body["sources"], list)
        assert isinstance(body["session_id"], str)

    def test_query_empty_string_is_accepted(self, client, mock_rag_system):
        response = client.post("/api/query", json={"query": ""})
        assert response.status_code == 200
        mock_rag_system.query.assert_called_once()


# ---------------------------------------------------------------------------
# GET /api/courses
# ---------------------------------------------------------------------------


class TestCoursesEndpoint:
    def test_courses_returns_analytics(self, client, sample_analytics):
        response = client.get("/api/courses")

        assert response.status_code == 200
        assert response.json() == sample_analytics

    def test_courses_delegates_to_rag_system(self, client, mock_rag_system):
        client.get("/api/courses")
        mock_rag_system.get_course_analytics.assert_called_once()

    def test_courses_error_returns_500(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = RuntimeError("chroma down")

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert "chroma down" in response.json()["detail"]

    def test_courses_empty_catalog(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        assert response.json() == {"total_courses": 0, "course_titles": []}

    def test_courses_rejects_post(self, client):
        response = client.post("/api/courses")
        assert response.status_code == 405


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


class TestRootEndpoint:
    def test_root_returns_ok(self, client):
        response = client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


class TestCORS:
    def test_cors_headers_present(self, client):
        response = client.get(
            "/api/courses", headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "*"


# ---------------------------------------------------------------------------
# Fixture sanity
# ---------------------------------------------------------------------------


class TestFixtures:
    def test_mock_rag_system_defaults(self, mock_rag_system, sample_analytics, sample_query_answer):
        assert mock_rag_system.get_course_analytics() == sample_analytics
        assert mock_rag_system.query("q", "s") == sample_query_answer

    def test_sample_course_titles_non_empty(self, sample_course_titles):
        assert len(sample_course_titles) > 0
        assert all(isinstance(t, str) for t in sample_course_titles)

    @pytest.mark.parametrize("path", ["/api/query", "/api/courses", "/"])
    def test_client_can_reach_all_routes(self, client, path):
        method = client.post if path == "/api/query" else client.get
        kwargs = {"json": {"query": "x"}} if path == "/api/query" else {}
        response = method(path, **kwargs)
        assert response.status_code == 200
