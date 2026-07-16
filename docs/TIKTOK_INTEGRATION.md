# TikTok Integration — Kadro

Kadro distinguishes several very different kinds of "TikTok access." Read this before
assuming any of them is available.

## 1. Authenticated access to your own account (production path)

Uses **TikTok Login Kit** (OAuth) for authorization and the **TikTok Display API** for
the authenticated user's own profile and video list. This requires:

- A TikTok developer app, approved for the scopes you need
  (`user.info.basic`, `video.list` at minimum).
- `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REDIRECT_URI` set in
  `apps/api/.env`.
- Completing the OAuth authorization-code flow once, so Kadro can store a refresh
  token in the `ExternalAccount` table.

Until those are configured and an OAuth token is stored, `TikTokLoginKitProvider`
(`apps/api/app/integrations/tiktok/production.py`) raises a clear
`TikTokNotConfiguredError` rather than silently returning empty or fake data. **Kadro
never pretends that typing in a username alone grants access to your video data** —
there is no "just scrape by username" path.

## 2. Public embed metadata (used for inspiration links)

TikTok's public oEmbed endpoint (`https://www.tiktok.com/oembed?url=...`) returns
title, author, thumbnail, and embed HTML for a public video URL without
authentication. Kadro's `InspirationContentResolver` Tier 1
(`apps/api/app/integrations/tiktok/resolver.py`) uses exactly this endpoint. This is
metadata only — no audio, no frames, no transcript.

## 3. Restricted research access

TikTok's Research API (separate program, separate approval, separate terms) is out of
scope for this MVP. It is not implemented, mocked, or referenced by any code path.

## 4. Optional, permitted media access

`AuthorizedMediaResolver` (Tier 2, `apps/api/app/integrations/tiktok/resolver.py`) is
an explicit, documented extension point for **media you are authorized to access** —
for example videos you download yourself and place under `MEDIA_STORAGE_PATH`, or a
future officially-sanctioned download mechanism. It is intentionally not implemented
against any live TikTok media endpoint in this MVP: **Kadro does not attempt to bypass
authentication, anti-bot protection, CAPTCHAs, rate limits, request signatures, or any
other access control**, and it never will as a "hidden requirement" of the product.

## 5. Metadata-only fallback (default reality for most inspiration links)

When Tier 1/2 cannot produce audio or frames, the resolver returns
`availability = "metadata_only"`. The item is still fully usable:

- the link, caption/title, author, and thumbnail are retained;
- your own Notion `Notes` are used as analysis input;
- the UI clearly labels the item `metadata_only`;
- no transcript or visual analysis is fabricated — the corresponding
  `ContentAnalysis` fields are `visual_analysis_available: false` /
  `transcript_available: false`, not invented values;
- the dashboard still shows the embedded TikTok player via the oEmbed embed HTML
  where TikTok supports it.

## Local development: mock adapter

`MockTikTokProvider` (`apps/api/app/integrations/tiktok/mock.py`) implements
`OwnContentProvider` entirely from `fixtures/tiktok_posts.json`, so the whole app runs
and is demonstrable with zero TikTok credentials. It is the default provider unless
`TIKTOK_CLIENT_KEY` etc. are configured and `AI_ENV` selects the production adapter.

## Sync behavior (both adapters)

`app/services/tiktok_sync.py` (used by both the mock and production adapter, since it
only depends on the `OwnContentProvider` protocol):

- stores `external_video_id` and skips re-processing videos whose ID + last-modified
  signal is unchanged since the last successful sync;
- records `SyncRun` rows with start/finish times, counts, and failures;
- paginates through `list_videos()` (the protocol supports a cursor internally);
- on an expired/revoked authorization (`TikTokAuthError`), marks the `SyncRun` failed
  with a clear message and leaves previously-synced data untouched — it never wipes
  existing `SourceVideo`/`OwnPost` rows because one sync failed.
