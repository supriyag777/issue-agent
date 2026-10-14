# AI GitHub Issue Agent

> Turn GitHub issues into actionable fixes with AI.

AI GitHub Issue Agent is a real full-stack developer tool that connects to a GitHub repository, retrieves live issues and bounded source context, analyzes an issue with OpenAI, and produces a human-reviewable patch. Repository writes are deliberately gated:

```text
Issue → Analysis → Proposed Patch → User Review → New Branch → Validation → Commit → Draft PR
```

The application never silently modifies `main`/`master`/the repository default branch and has no merge action.

## Features

- React + TypeScript + Vite developer-control-room frontend.
- FastAPI + Pydantic + SQLAlchemy backend.
- PostgreSQL in Docker Compose, with an explicit SQLite fallback for Preview demo mode.
- JWT authentication with Argon2 password hashing.
- GitHub PAT connection with server-side-only credential handling.
- Live repository metadata, issues, labels, comments, and issue filters.
- Keyword extraction, GitHub code search, relevant-file ranking, and bounded code chunks.
- OpenAI structured JSON analysis validated by Pydantic.
- Reviewable proposed changes and unified diff.
- Explicit approval, non-default branch creation, structural/test validation, commit, and draft PR sequence.
- Provider-unavailable and demo states are visible instead of hidden behind fake core data.
- Structured request logging that omits passwords, tokens, API keys, and authorization headers.
- Persistent in-product AI Guide with built-in contextual help and optional OpenAI answers with safe fallback.

## Architecture

```text
React/Vite → FastAPI → SQLAlchemy → PostgreSQL
                 ├── GitHub REST API
                 └── OpenAI Chat Completions

Issue → bounded code search → structured analysis → diff → human gate
     → safe branch → validation → commit → draft pull request
```

See `docs/architecture.md`, `docs/api.md`, `docs/security.md`, and `docs/ai-workflow.md` for details.

## Environment setup

Copy the example file and set a strong secret:

```bash
cp .env.example .env
```

Important variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL DSN in production/Docker; SQLite is supported only for explicit Preview demo fallback. |
| `JWT_SECRET` | Long random secret for application JWTs. |
| `TOKEN_ENCRYPTION_KEY` | Optional Fernet key for encrypting GitHub PATs; generate with `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`. |
| `DEMO_MODE` | `true` enables clearly labeled demo provider data when credentials are unavailable; use `false` for live-only behavior. |
| `GITHUB_API_URL` | Normally `https://api.github.com`. |
| `OPENAI_API_KEY` | Server-only OpenAI key. Never place it in frontend variables. |
| `OPENAI_MODEL` | Model used for structured analysis, default `gpt-4o-mini`. |
| `TEST_COMMAND` | Optional repository test command used when a configured worktree is available. |
| `REPOSITORY_WORKTREE_ROOT` | Optional local checkout root for executing configured tests. |

## Run with Docker

Docker Compose starts PostgreSQL, FastAPI, and Vite:

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/api/docs`
- Health: `http://localhost:8000/health`

Docker uses PostgreSQL. Do not put secrets into the image or commit `.env`.

## Run locally

Backend:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

If Corepack/pnpm is healthy, `pnpm install` and `pnpm dev` are also supported. The repository pins the intended pnpm version, while npm remains a compatible fallback for restricted sandboxes.

For the complete Windows PowerShell process—including Python setup, separate backend/frontend terminals, GitHub PAT creation, live repository connection, port troubleshooting, log inspection, and safe shutdown—see [`WINDOWS_RUN_GUIDE.md`](WINDOWS_RUN_GUIDE.md).

## GitHub setup

Create a fine-grained GitHub PAT with only the repository permissions required for the selected workflow (metadata/issues/content read, and contents/pull requests write only when branch/commit/draft-PR operations are intended). Enter it on the Repositories screen with demo mode disabled. The backend validates the requested repository and stores an encrypted value; the token is never sent back to the browser.

## OpenAI setup

Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` on the backend only. The AI receives issue information plus bounded, relevant source chunks—not the whole repository. The response must be JSON matching the Pydantic `AnalysisResult` contract. Invalid or unavailable provider responses stop the workflow rather than creating an unvalidated patch.

## Complete workflow test

1. Register a local account.
2. Connect a repository in demo mode, or enter a GitHub PAT for live mode.
3. Open the repository dashboard and filter issues.
4. Open an issue and select **Analyze with AI**.
5. Review the summary, root-cause hypothesis, bounded code context, plan, and diff.
6. Select **Approve proposed patch**.
7. Create the safe branch, validate the patch/tests, commit, and create the draft PR in sequence.
8. Confirm that no action targets the default branch and that the draft PR URL is displayed.

Backend tests cover this demo flow:

```bash
.venv/bin/pytest -q
```

Frontend checks:

```bash
cd frontend
npm run build
npm test
```

## Known limitations

- GitHub OAuth is not implemented; PAT is the initial connection method.
- Live repository test execution requires a configured local worktree and `TEST_COMMAND`; without that, structural validation is explicit and visible.
- Applying AI-generated `new_content` is intentionally conservative. Unified-diff-only proposals without complete replacement content are displayed for review but are not applied automatically.
- Demo mode uses deterministic sample provider data and is labeled in the UI. It is not a substitute for live provider verification.
- Docker is the authoritative PostgreSQL path; the sandbox Preview may use SQLite when the managed runtime injects an incompatible DSN.

## Interview explanation

This project demonstrates provider isolation, bounded context selection, structured AI output, server-side secrets, authenticated ownership, safe-path validation, explicit state transitions, and a human-in-the-loop repository mutation boundary. The most important design choice is that the AI does not receive an execution tool: it proposes data, while explicit application endpoints enforce every side effect.

## Project structure

- `frontend/`: React/Vite UI, typed API client, route pages, guarded workflow controls.
- `backend/app/api/`: authenticated FastAPI routes.
- `backend/app/services/`: GitHub, code search, AI, and patch services.
- `backend/app/models/` and `backend/app/db/`: SQLAlchemy persistence.
- `database/`: migration scaffolding.
- `docs/`: architecture, API, database, security, AI, GitHub, and interview documentation.
