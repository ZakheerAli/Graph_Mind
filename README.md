# GraphMind

GraphMind lets users upload documents and ask questions that are answered with source citations. The product roadmap starts with normal retrieval-augmented generation (RAG), then adds keyword and knowledge-graph retrieval.

## Project layout

- `apps/api` — FastAPI service
- `apps/web` — Next.js web application
- `docs` — specification, architecture, and project progress
- `infra/migrations` — database migrations
- `eval` — evaluation data and results

## Local development

1. Copy `.env.example` to `.env` and set local values as needed. Never commit `.env`.
2. Install the API: `python -m pip install -e "apps/api[dev]"`
3. Install the web app: `npm --prefix apps/web install`
4. Run the API from `apps/api`: `python -m uvicorn app.main:app --reload`
5. Run the web app: `npm --prefix apps/web run dev`
6. Run all checks from the project root: `make check`

The API listens on port 8000. Liveness and readiness are available at `/health` and `/ready`. AI features are disabled by default; integrations are introduced in later phases.

## Project rules and scope

Read [the specification](docs/SPEC.md), [architecture](docs/ARCHITECTURE.md), and [agent instructions](AGENTS.md) before making changes. `docs/PROGRESS.md` tracks the current phase and exact next task.
