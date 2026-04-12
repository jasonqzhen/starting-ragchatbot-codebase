# Testing Framework Enhancements

> Note: This task produced backend testing infrastructure (not frontend code).
> Per the task instructions, the summary of changes is recorded here in
> `frontend-changes.md`.

## Summary

Added API-level testing infrastructure for the RAG system so the FastAPI
endpoints (`/api/query`, `/api/courses`, `/`) are exercised in CI without
pulling in the real `RAGSystem`, ChromaDB, or the `../frontend` static mount.

All 19 new tests pass via `uv run pytest`.

## Files added

### `backend/tests/__init__.py`
Empty marker so `backend/tests` is importable as a package.

### `backend/tests/conftest.py`
Shared pytest fixtures:

- **`sample_course_titles`, `sample_analytics`, `sample_query_answer`** —
  canned test data used across endpoint tests.
- **`mock_rag_system`** — `MagicMock` that mirrors the surface of
  `RAGSystem` the API touches (`session_manager.create_session`, `query`,
  `get_course_analytics`).
- **`test_app`** — builds a standalone `FastAPI` app in
  `_build_test_app(rag_system)` that mirrors the endpoints in
  `backend/app.py` but:
  - omits the `StaticFiles` mount on `../frontend` (which doesn't exist
    in the test environment and would break `TestClient` startup),
  - injects the mocked RAG system instead of constructing the real one,
  - adds a simple `GET /` route so tests can cover the root path without
    loading the real frontend assets.
- **`client`** — a `fastapi.testclient.TestClient` bound to `test_app`.

`conftest.py` also prepends `backend/` to `sys.path` so the tests can
import backend modules when invoked from the repo root.

### `backend/tests/test_api_endpoints.py`
19 tests across 6 classes:

- **`TestQueryEndpoint`** — `/api/query`
  - creates a session when none provided
  - reuses an explicit `session_id`
  - returns 422 on missing field / wrong type
  - returns 500 when `rag_system.query` raises
  - response schema shape check
  - accepts empty-string query
- **`TestCoursesEndpoint`** — `/api/courses`
  - returns analytics payload
  - delegates to `rag_system.get_course_analytics`
  - returns 500 on backend error
  - handles empty catalog
  - rejects `POST` with 405
- **`TestRootEndpoint`** — `/` returns ok status
- **`TestCORS`** — CORS middleware emits `access-control-allow-origin`
- **`TestFixtures`** — sanity checks on the fixtures themselves, plus a
  parametrized smoke test that every route is reachable via the client

## Files modified

### `pyproject.toml`
- Added a `[dependency-groups]` `dev` group with `pytest>=8.0` and
  `httpx>=0.27` (httpx is required by `fastapi.testclient.TestClient`).
- Added `[tool.pytest.ini_options]`:
  - `testpaths = ["backend/tests"]`
  - `pythonpath = ["backend"]` so tests can `import` backend modules
    without needing an installed package
  - `python_files`/`python_classes`/`python_functions` conventions
  - `addopts = ["-ra", "--strict-markers", "--tb=short"]`
  - `filterwarnings` to silence deprecation noise from dependencies

## How to run

```bash
uv sync --group dev
uv run pytest
```

Expected: `19 passed`.

## Design notes

- **Why a separate test app instead of importing `backend/app.py`?**
  `backend/app.py` constructs `RAGSystem(config)` at import time (which
  spins up ChromaDB and needs an `ANTHROPIC_API_KEY`) and mounts
  `../frontend` as static files. Both break cleanly under `TestClient`.
  A standalone app that mirrors the route definitions lets us inject a
  mock and keeps the tests hermetic.
- **Why `MagicMock` instead of a real `RAGSystem`?** The endpoint tests
  are about request/response handling — schema validation, status codes,
  error propagation, session wiring — not retrieval quality. Unit tests
  for the RAG internals belong in separate test modules.
- **Fixture scope.** All fixtures are function-scoped so each test gets a
  fresh mock and a fresh client; this avoids cross-test bleed on the
  `MagicMock` call history that tests assert against.
