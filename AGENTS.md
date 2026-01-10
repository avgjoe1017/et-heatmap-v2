# Repository Guidelines

## Project Structure & Module Organization
- `src/` houses the Python backend (FastAPI app in `src/app`, pipeline in `src/pipeline`, NLP in `src/nlp`, storage/DAO in `src/storage`).
- `ui/` contains the React + TypeScript frontend (`ui/src/components`, `ui/src/pages`, `ui/src/api`).
- `tests/` contains pytest suites, with longer-running coverage in `tests/integration`.
- `config/`, `schemas/`, and `data/` store runtime configuration, API schemas, and local SQLite data; `scripts/` includes operational helpers.

## Build, Test, and Development Commands
- `pip install -e .` installs backend dependencies for local dev.
- `python scripts/setup.py` initializes the database and seeds required entities.
- `python scripts/run_api.py` starts the FastAPI server at `http://localhost:8000`.
- `python scripts/run_pipeline.py` runs a daily ingestion + scoring pass.
- `cd ui && npm install && npm run dev` launches the Vite frontend at `http://localhost:5173`.
- `make up`, `make down`, `make test`, `make lint` run Docker-based dev, tests, and linting via `docker-compose`.

## Coding Style & Naming Conventions
- Python formatting uses Black (line length 100) with Ruff for linting; keep modules in `snake_case`.
- TypeScript/React uses ESLint; component files are `PascalCase.tsx` (see `ui/src/components`).
- Prefer small, focused modules and keep API schema changes aligned with `schemas/`.

## Testing Guidelines
- Tests are run with pytest; naming follows `test_*.py` and `Test*` classes (see `pytest.ini`).
- Use markers like `@pytest.mark.integration` for slow or external-service coverage.
- `make test-coverage` generates HTML coverage for backend changes.

## Commit & Pull Request Guidelines
- Git history is minimal and does not enforce a formal message format; keep messages short and descriptive (imperative preferred).
- PRs should explain the change, list test commands run, and include UI screenshots for frontend-visible updates.

## Configuration & Secrets
- Copy `.env.example` to `.env` and keep API keys local; never commit secrets.
- When running locally, verify config with `python scripts/validate_config.py`.