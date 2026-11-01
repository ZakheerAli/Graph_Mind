# PROGRESS.md - the project memory (update at the end of EVERY session)

Last updated: 2026-10-26
Current phase: Phase 1 - Ingest + vector search

## Done
- P0 scaffold is present: API, web app, configuration, health endpoints, CI, and `make check`.
- Added the initial documents/chunks migration with owner RLS, cascading deletion, pgvector, and full-text indexes.
- Added a PostgreSQL document/chunk adapter that persists extracted chunks, scopes reads and deletes by user, and relies on the document foreign key for chunk cascading.
- Document service uses PostgreSQL when `DATABASE_URL` is configured and keeps in-memory storage for development only.
- Added adapter tests for persisted chunk data and owner-scoped queries.

## In progress
- Add a database-backed integration test for upload persistence, user isolation, and cascading deletion.

## NEXT task (exact, small, one session)
- Verify upload persistence and cascade behavior against a configured PostgreSQL/Supabase test database.

## Decisions made (short; details in docs/DECISIONS/)
- PostgreSQL persistence uses psycopg; local development can use the existing in-memory adapter when no database URL is configured.

## Task history
- 2026-10-26: Implemented PostgreSQL-backed document/chunk persistence and owner-filtered reads/deletes; added adapter tests. API tests (8 passed), changed-file Ruff checks, and web lint passed. `make check` could not run because `make` is unavailable; full Ruff reports existing violations in `documents.py` router and `schemas/documents.py`.

## Known issues / risks
- Workspace has no Git metadata, so branch creation and `git status`/`git log` are unavailable.
- No configured database was available to run a PostgreSQL integration test; the adapter is verified with unit tests only.
- Original upload binaries are not yet written to Supabase Storage; the database currently records the expected storage key while extracted chunks are persisted.
- Embeddings are not yet persisted; the schema supports them, but embedding generation is not implemented.

## How to run
- API: cd apps/api && uvicorn app.main:app --reload
- Web: cd apps/web && npm run dev
- Checks: make check
- Env: copy .env.example to .env and fill values (never commit .env)

## Phase checklist
- [ ] P0 Setup  - [ ] P1 Ingest + vector search  - [ ] P2 Chat + citations + UI
- [ ] P3 Auth + RLS + eval baseline  - [ ] P4 Knowledge graph  - [ ] P5 Hybrid + eval comparison
- [ ] P6 Harden + deploy + docs
