# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A FastAPI service for uploading Markdown notes, running grammar checks, converting them to HTML, and persisting the results. Pipeline: upload → grammar check → save → list/render as HTML.

## Tooling

- Python `>=3.14` (pinned via `.python-version` → 3.14). Package + venv management uses **uv** (see `uv.lock`).
- Web framework: **FastAPI** with the `[standard]` extra (so `uvicorn`, `httpx`, and the `fastapi` CLI are present).
- Markdown rendering: the `markdown` package (`markdown.markdown(...)`).
- Grammar: `language-tool-python` (`LanguageTool`). Note: this downloads a Java-based LanguageTool server on first use, so first run is slow and needs a JRE available. The instance is created once at startup in `lifespan` and shared via the module-level `tools` dict.

## Common commands

```powershell
# Install / sync deps (creates .venv)
uv sync

# Activate venv (PowerShell)
.venv\Scripts\Activate.ps1

# Run the API in dev (reload). Either:
uv run python main.py
# or
uv run fastapi dev main.py

# Run tests (once pytest is added as a dev dependency)
uv run pytest
```

There is no linter or formatter configured in `pyproject.toml` — don't invent commands for them; add them deliberately if needed. `pytest` is not yet a dependency; add it with `uv add --dev pytest` before running tests.

## Architecture notes

- `main.py` is the whole app: a single FastAPI `app` whose `lifespan` creates `./checked_markdown_files/` and a shared `LanguageTool("en-US")` instance (stored in the module-level `tools` dict, closed on shutdown).
- Endpoints:
  - `POST /check` — accepts an `UploadFile`, validates the extension via regex (`.md` / `.markdown`, case-insensitive, see `is_markdown_file`), and returns LanguageTool matches as `{"grammatical_errors": [...]}`.
  - `POST /save` — accepts a plain-text body, names the file `abs(hash(text)).md`, and writes it into `checked_markdown_files/`. Note: `hash()` is salted per process in Python, so the same text produces different filenames across runs.
  - `GET /notes` — lists saved files, returning the `SavedNotes` Pydantic model (`schema.py`), or a plain string message when the directory is empty.
  - `GET /note/{filename}` — reads `<filename>.md`, renders it to HTML via `markdown.markdown`, returns `HTMLResponse`; returns a JSON error (but with status 200) if the file is missing.
- `schema.py` holds Pydantic response models (currently just `SavedNotes`).
- `tests.py` is the test module (pytest-style, uses `fastapi.testclient.TestClient`). It currently contains only a stub. Heads-up: it uses a relative import (`from .main import app`) which fails when the project root is not a package — use `from main import app` when running pytest from the project root.
- `checked_markdown_files/` holds persisted notes; treat its contents as data, not source. Tests should not depend on or pollute real files in it.
- `random.txt` is a leftover scratch artifact; safe to ignore or delete.
- `README.md` is an empty placeholder.

## Testing guidance

- Use `TestClient` from `fastapi.testclient` for endpoint tests. Prefer `with TestClient(app) as client:` so the `lifespan` runs — but note that the real lifespan boots LanguageTool (slow, needs Java). For fast unit tests, override or monkeypatch the `tools` dict / `grammar_check` instead of starting the real LanguageTool.
- Point `markdown_dir` at a `tmp_path` (monkeypatch the module attribute) so tests never touch `checked_markdown_files/`.