# Data Model — Kadro

All tables use UUID primary keys (`uuid4`, generated in Python), timezone-aware
`created_at`/`updated_at` timestamps, and keep external platform IDs in dedicated
unique columns rather than reusing them as primary keys. See
`apps/api/app/models/` for the SQLAlchemy source of truth; this document is a guide,
not a duplicate schema.

## Entities

- **UserSettings** — singleton-per-install row: `tiktok_username`,
  `default_output_language`, idea-mixture weights, `similarity_threshold`, AI model
  names (never secret values), Notion sync toggle/interval, and
  `notion_database_id` (auto-discovered/auto-provisioned by
  `NotionDatabaseProvisioner` — never entered manually, see `docs/NOTION_SETUP.md`).
- **ExternalAccount** — an OAuth-connected account (`provider` = `tiktok`), stores
  token metadata (expiry, scope) but never the raw token in a field that is ever
  serialized to the frontend; token material is written to a column excluded from all
  response schemas.
- **CreatorProfile** — denormalized profile info fetched from `OwnContentProvider`
  (display name, avatar URL, follower count, bio) tied to an `ExternalAccount`.
- **ContentFormat** — reference table of recognized formats (`code`, `label_en`,
  `label_lt`, `description`), seeded and extendable without an enum change.
- **SourceVideo** — a raw synced video from the creator's own account before/along
  with analysis: `external_video_id` (unique), `permalink`, `caption`, `posted_at`,
  `duration_seconds`, `stats` (JSON), `sync_run_id`.
- **OwnPost** — one-to-one with `SourceVideo`; the analyzed, profile-facing
  representation (`processing_status`, link to `ContentAnalysis`).
- **InspirationItem** — a Notion-sourced inspiration link: `notion_page_id` (unique),
  `title`, `tiktok_url` (normalized), `tiktok_video_id` (nullable, unique when
  present), `creator_name`, `topics` (list, optional hint back-filled by Kadro),
  `format_hint` (optional hint back-filled by Kadro), `note_why_saved`,
  `note_favorite_part`, `notion_status`, `availability`
  (`full_media`/`transcript_only`/`metadata_only`/`unavailable`), `processed_at`,
  `error_message`. Field names mirror the auto-provisioned Notion schema in
  `docs/NOTION_SETUP.md`.
- **MediaAsset** — a downloaded/derived media file (audio extract, sampled frame) with
  `kind`, `storage_path`, `size_bytes`, `mime_type`, owning `OwnPost` or
  `InspirationItem`.
- **Transcript** — `source_type` (`own_post`/`inspiration_item`), `language_detected`
  (`lt`/`en`/`mixed`/`unknown`), `text`, `is_original_language`.
- **ContentAnalysis** — the structured schema described in the brief
  (`primary_topic`, `secondary_topics`, `content_format`, `presentation_style`, `hook`,
  `tone`, `story_structure`, `audience_promise`, `editing_intensity`,
  `estimated_pacing`, `personal_story_level`, `educational_level`,
  `visual_analysis_available`, `transcript_available`, `confidence`), one row per
  `OwnPost` or `InspirationItem`, plus an `embedding` vector column.
- **ContentProfileSnapshot** — a versioned, timestamped rebuild of the derived
  profile (pillars, format distribution, hook patterns, gaps, confidence, sample
  size) so history is preserved rather than overwritten in place.
- **ContentIdea** — a generated idea with all fields from the brief's idea JSON shape,
  plus `status` (`proposed`/`saved`/`archived`) and `output_language`.
- **IdeaSource** — join table linking a `ContentIdea` to the `OwnPost`/`InspirationItem`
  rows retrieved as context for it, with a `role` (`identity_reference`,
  `inspiration_reference`, `similarity_neighbor`).
- **IdeaFeedback** — `rating` (`love`/`maybe`/`not_for_me`/`already_covered`),
  optional free-text `comment`, tied to a `ContentIdea`.
- **GeneratedBrief** — the full Lithuanian production-brief JSON for an idea.
- **GeneratedScript** — the full spoken script text plus `mode`
  (see `docs/AI_PIPELINE.md`), separated into `spoken_lines` and `editing_notes`.
- **SyncRun** — one row per Notion or TikTok sync invocation: `source`
  (`notion`/`tiktok`), `status`, `started_at`, `finished_at`, `items_processed`,
  `items_failed`, `error_summary`.
- **ProcessingJob** — the database-backed job abstraction described in
  `docs/ARCHITECTURE.md`: `job_type`, `status`, `payload`, `result`, `error`,
  `related_entity_type`/`related_entity_id`.

## Relationships (high level)

```text
ExternalAccount 1--1 CreatorProfile
CreatorProfile 1--N SourceVideo
SourceVideo 1--1 OwnPost 1--1 ContentAnalysis
InspirationItem 1--1 ContentAnalysis
OwnPost / InspirationItem 1--N MediaAsset
OwnPost / InspirationItem 0--1 Transcript
ContentIdea N--M (OwnPost | InspirationItem) via IdeaSource
ContentIdea 1--N IdeaFeedback
ContentIdea 0--1 GeneratedBrief
ContentIdea 0--1 GeneratedScript
SyncRun 1--N SourceVideo | InspirationItem (via sync_run_id)
```

## Vector storage

`ContentAnalysis.embedding` uses the dialect-aware `Vector(dim)` type
(`app/db/types.py`): a real `pgvector` column on Postgres, a JSON-encoded `Text`
column on SQLite (test/sandbox fallback). See `docs/ARCHITECTURE.md` for why.
