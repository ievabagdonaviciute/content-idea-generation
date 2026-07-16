# Architecture — Kadro

## Overview

```text
apps/web (Next.js/TS)  ---HTTP/JSON--->  apps/api (FastAPI)  --->  PostgreSQL + pgvector
                                                |
                                                +--> integrations/notion (Notion API)
                                                +--> integrations/tiktok (Login Kit + Display API, mock adapter)
                                                +--> ai (transcription / vision / embeddings / text providers)
```

The backend is a modular monolith. Each concern (Notion, TikTok, AI, pipelines) is
isolated behind a Python `Protocol` interface with at least one deterministic fake
implementation, so the whole system runs and is testable without any external
credentials.

## Backend layering

```text
api/v1/*        FastAPI routers. Thin: parse request, call a service, map to a response schema.
services/*      Business logic. Own transactions. Call repositories and providers.
repositories/*  Query/persistence helpers for entities where a plain query would be
                repeated across services (posts, inspiration, ideas, sync runs).
integrations/*  Notion client, TikTok adapters (mock + production scaffold).
ai/*            Provider Protocols + fake providers + one OpenAI-compatible provider.
pipelines/*     The explicit ingest -> normalize -> acquire -> transcribe -> sample ->
                analyze -> embed -> mark-status pipeline, as small composable functions.
models/*        SQLAlchemy 2 declarative models (one module per aggregate area).
schemas/*       Pydantic v2 request/response and structured-AI-output models.
core/*          Settings, logging, security helpers, shared constants (incl. app name).
db/*            Engine/session setup, the dialect-aware Vector type.
```

Dependency direction is strictly top-to-bottom: routers depend on services; services
depend on repositories/integrations/ai/pipelines; nothing below `services/` imports
FastAPI.

## Provider interfaces

- `OwnContentProvider` (`integrations/tiktok/base.py`) — `get_profile()`,
  `list_videos()`. Implementations: `MockTikTokProvider` (fixtures-backed),
  `TikTokLoginKitProvider` (scaffold; raises a clear configuration error until
  `TIKTOK_CLIENT_KEY`/`TIKTOK_CLIENT_SECRET`/`TIKTOK_REDIRECT_URI` and a stored OAuth
  token are present).
- `InspirationContentResolver` (`integrations/tiktok/resolver.py`) — `resolve(url)` ->
  `ResolvedInspirationContent` with `availability` in
  `{full_media, transcript_only, metadata_only, unavailable}`. Tier 1 uses TikTok's
  public oEmbed endpoint (`www.tiktok.com/oembed`) for title/author/thumbnail/embed
  HTML. Tier 2 (`AuthorizedMediaResolver`) is an explicit optional interface that is
  not wired to any unofficial scraping; it is left as a documented extension point.
  Tier 3 always applies when Tier 1/2 do not yield audio/frames.
- `NotionInspirationClient` (`integrations/notion/client.py`) — queries/updates the
  inspiration database. `MockNotionClient` reads/writes an in-memory or
  fixture-backed list for local dev; `NotionClient` uses the real Notion REST API via
  `httpx`. The database itself is never manually configured: `NotionPageUrl` and the
  database title are hardcoded in `core/personal_config.py`, and
  `NotionDatabaseProvisioner` (`integrations/notion/provisioner.py`) finds-or-creates
  the database inside that page and ensures its property schema on every sync,
  caching the discovered ID on `UserSettings.notion_database_id`. See
  `docs/NOTION_SETUP.md`.
- AI providers (`ai/base.py`): `TranscriptionProvider`, `VisionAnalysisProvider`,
  `EmbeddingProvider`, `TextGenerationProvider`. Each has a `Fake*` implementation
  (deterministic, seeded from input text so tests are stable) and the app wires either
  fakes or `OpenAICompatibleProvider` based on `AI_API_KEY` presence.

## Processing jobs (no queue)

`ProcessingJob` rows record `job_type`, `status`
(`pending`/`processing`/`completed`/`failed`), `payload`, `result`, `error`, and
timestamps. Sync/analysis services create a job row, run synchronously in-process
(this is a local personal app; volumes are small), and update the row's status/result.
This keeps the state machine identical to what a real worker would use, so a queue
consumer could be added later by having it claim `pending` jobs instead of running
inline — no schema or API change required.

## Database: Postgres/pgvector in production, SQLite in tests

The brief specifies PostgreSQL + pgvector. This sandbox has neither Docker nor a local
Postgres server available, so the automated test suite runs against SQLite
(`aiosqlite`) instead. To keep one model definition working on both:

- `app/db/types.py` defines `Vector(dim)`, a `TypeDecorator` that binds to
  `pgvector.sqlalchemy.Vector` on the `postgresql` dialect and to a `Text` column
  (JSON-encoded float list) elsewhere, with cosine similarity computed in Python for
  the SQLite fallback (`app/services/similarity.py`).
- Alembic migrations target Postgres (they call `CREATE EXTENSION IF NOT EXISTS
  vector` and use `sa.dialects.postgresql` types). SQLite-based tests instead call
  `Base.metadata.create_all` against an in-memory engine, which is standard practice
  for SQLAlchemy test suites and does not depend on Alembic.
- `docker-compose.yml` still provisions real `pgvector/pgvector:pg16` for local
  development; anyone running the project outside this sandbox should use Postgres via
  Docker Compose as documented in the README, not SQLite.

This is the one deliberate structural deviation from the brief's stack list, made
necessary by the sandbox environment rather than by preference, and it does not change
any model, schema, or API contract.

## Frontend

Next.js App Router, TypeScript, Tailwind, TanStack Query for server state. API access
goes through a single typed client (`apps/web/lib/api.ts`) built from hand-written
TypeScript types in `apps/web/types/` that mirror the backend Pydantic schemas (kept
aligned by convention and covered by an API contract smoke test, not by codegen, to
avoid adding a build-time dependency for the MVP).

UI copy lives in `apps/web/lib/strings.ts` (English for the MVP UI chrome) so
localization is a matter of adding a second strings module and a switch, without
touching components. Creator-generated content (ideas, briefs, scripts) is rendered
verbatim in whatever language it was generated in — Lithuanian by default.

## Security boundaries

- Secrets only via environment variables (`.env`, git-ignored); `.env.example` has
  placeholders only.
- No access tokens or AI API keys are ever included in an API response body.
- `InspirationContentResolver` and the Notion URL validator restrict outbound requests
  to an allow-list of hosts (`tiktok.com`, `www.tiktok.com`, `vm.tiktok.com`,
  `m.tiktok.com`) to reduce SSRF risk, apply a request timeout, and cap response size.
- FFmpeg is invoked via `asyncio.create_subprocess_exec` with an argument list (never
  a shell string), so there is no shell interpolation.
