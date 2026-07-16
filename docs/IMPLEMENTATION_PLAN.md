# Implementation Plan — Kadro

This document tracks the build plan for Kadro, a personal AI-assisted TikTok content
planning platform. It is the single source of truth for phase scope and status while
the MVP is being built.

## Guiding constraints

- No orchestration frameworks (LangChain/LangGraph/CrewAI/LlamaIndex). Plain Python
  services with explicit pipelines.
- No Redis/Celery/Kafka for the MVP. A database-backed processing-job table plus
  synchronous/CLI-triggered execution stands in for a worker queue. The `ProcessingJob`
  model and service boundary are designed so a real worker can be swapped in later
  without changing callers.
- Everything must run and be demonstrable with zero external credentials, using mock
  TikTok/Notion adapters and deterministic fake AI providers.
- Generated creator-facing content defaults to natural Lithuanian. UI chrome is English
  for the MVP but all UI strings are centralized in one module for later localization.
- Postgres + pgvector is the target production database. Because this sandbox has no
  local Postgres/Docker available, the backend also runs against SQLite for tests and
  quick local checks: a dialect-aware `Vector` column type stores embeddings as JSON on
  SQLite and as `vector(N)` on Postgres. This is documented in `docs/ARCHITECTURE.md`
  as a deliberate deviation with a stated reason.

## Repository layout

Matches the structure requested in the brief (`apps/api`, `apps/web`, `docs`,
`fixtures`, `scripts`, `docker-compose.yml`, `.env.example`, `Makefile`). See
`docs/ARCHITECTURE.md` for the rationale behind any deviations.

## Phases

1. **Foundation** — repo scaffold, docs, backend app skeleton, config, DB engine,
   domain models, Alembic migration, health endpoint, Docker Compose, seed fixtures.
2. **Notion inspiration inbox** — Notion client + mock adapter, sync pipeline
   (New -> Processing -> Processed/Failed), duplicate/URL normalization, CLI command,
   tests.
3. **TikTok own-content sync** — `OwnContentProvider` protocol, mock adapter, sync
   service with incremental sync + pagination + revoked-auth handling, production
   adapter scaffold (TikTok Login Kit + Display API), tests.
4. **AI analysis pipeline** — provider interfaces (transcription, vision/multimodal,
   embeddings, text generation) with fake deterministic implementations and one
   OpenAI-compatible implementation, structured `ContentAnalysis` schema + repair-retry
   validation, embeddings + pgvector/SQLite similarity search, content profile builder.
5. **Idea generation** — retrieval-based idea generator with configurable novelty
   mixture, similarity/duplicate categorization, feedback storage, brief generation,
   script generation, REST endpoints for all of the above.
6. **Frontend** — Next.js dashboard with all required pages, TanStack Query API layer,
   loading/empty/error states, embedded TikTok display where available.
7. **Verification** — run backend tests/lint/type-check, run frontend
   lint/type-check/build, fix gaps, write final gap report in the closing message.

## Status

- [x] Phase 1
- [x] Phase 2
- [x] Phase 3
- [x] Phase 4
- [x] Phase 5
- [x] Phase 6
- [x] Phase 7 (see final report in conversation for outstanding gaps)
