# Privacy and Security — Kadro

Kadro is a local, single-user personal application. This document states what data it
stores, where, and the controls in place.

## What is stored

- **Your TikTok content**: captions, permalinks, posted dates, stats, and (when
  full-media access is available) extracted audio/frames and transcripts, in
  `MEDIA_STORAGE_PATH` (default `./data/media`) and the database.
- **Notion inspiration links**: URL, creator, your notes, status, and derived
  analysis. Kadro never deletes or overwrites your Notion rows' `Name`/`TikTok URL`/
  `Creator`/`Notes` — it only ever writes `Status`, `Processed At`, and `Error`.
- **Generated content**: ideas, briefs, scripts, and your feedback on them.
- **Settings**: your TikTok username, language/mixture/threshold preferences, and
  which AI model names are configured (not the key itself — see below).

## What is never stored in a readable/exposed way

- Raw OAuth access/refresh tokens and the AI API key are only ever read from
  environment variables or, for OAuth tokens, written to a database column that is
  excluded from every Pydantic response schema (`ExternalAccount.access_token` uses
  `Field(exclude=True)` equivalents at the schema layer — the ORM column exists, but no
  API response ever serializes it).
- No secret value is logged. `app/core/logging.py` configures structured logging with
  a redaction filter for keys named `*token*`, `*secret*`, `*api_key*`.

## Network/SSRF controls

- Inspiration URL validation (`app/core/url_validation.py`) only allows
  `ALLOWED_INSPIRATION_HOSTS` (default: `tiktok.com`, `www.tiktok.com`,
  `vm.tiktok.com`, `m.tiktok.com`) and rejects anything else — including bare IPs and
  `localhost` — before any outbound request is made.
- All outbound HTTP (Notion, TikTok oEmbed, AI provider) goes through `httpx.AsyncClient`
  with an explicit timeout (`HTTP_TIMEOUT_SECONDS`, default 15s).
- Downloaded media is capped by `MAX_MEDIA_SIZE_MB` (default 200MB), enforced by
  checking `Content-Length` and aborting a stream that exceeds the cap.
- MIME types of downloaded/derived media are validated against an allow-list before
  being handed to FFmpeg.

## FFmpeg invocation

FFmpeg is always invoked with `asyncio.create_subprocess_exec(*argv)` — an explicit
argument list, never a shell string — so there is no shell interpolation regardless of
what a caption, filename, or URL contains.

## Deleting your data

```bash
cd apps/api
python -m app.cli purge-local-data
```

This deletes all rows from every table and removes everything under
`MEDIA_STORAGE_PATH`, after an interactive confirmation prompt (skip the prompt with
`--yes` for scripted use). It does not touch your Notion database or your TikTok
account — those are the systems of record you control directly.

## Authentication

The MVP has no login system: it is designed to run on your own machine for your own
account. `UserSettings` is a single row, not a per-user table, but every model already
carries the fields needed (timestamps, no assumption of a global mutable singleton in
business logic beyond that one settings row) so a real auth layer could be introduced
later without a full rewrite.
