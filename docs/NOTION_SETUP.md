# Notion Setup — Kadro inspiration inbox

Kadro is a personal, single-user tool. It does not have a Notion setup wizard, does
not ask for a database URL or ID anywhere in the UI or CLI, and will not ask again
after you add your token once. The target Notion page and the database name are
hardcoded in `apps/api/app/core/personal_config.py`:

```python
NOTION_PAGE_URL = "https://app.notion.com/p/Content-Inspo-39e4386daefa80779e82cc34b5796aaf"
NOTION_INSPIRATION_DATABASE_TITLE = "TikTok Inspiration"
```

If you ever move the inspiration database to a different page, edit that file and
restart the backend — that is the only place this ever needs to change.

## 1. Create a Notion integration and share the page

1. Go to https://www.notion.so/my-integrations and create a new internal
   integration. Copy the "Internal Integration Secret" — this is `NOTION_TOKEN`.
2. Open the page at `NOTION_PAGE_URL` in Notion, click "..." → "Connections", and
   add your integration so it can read/write inside that page. This is the only
   manual Notion step. You do not need to create the database yourself.

## 2. Set the token

In `apps/api/.env` (git-ignored — never commit this file):

```env
NOTION_TOKEN=secret_your_internal_integration_token
```

`NOTION_TOKEN` is the only Notion-related environment variable. There is no
`NOTION_DATABASE_ID` to configure — Kadro finds or creates the database itself.

Leave `NOTION_TOKEN` empty to keep using the bundled mock adapter
(`MockNotionClient`), which reads fixture data from `fixtures/notion_items.json` and
lets you exercise the full sync pipeline with zero Notion account.

## 3. What happens automatically on first sync

`NotionDatabaseProvisioner` (`apps/api/app/integrations/notion/provisioner.py`) runs
this idempotent sequence the first time a Notion sync executes (and re-verifies it on
every later sync, cheaply):

1. Read `NOTION_TOKEN` from the environment.
2. Read the hardcoded `NOTION_PAGE_URL` and extract the Notion page ID from it.
3. Connect to the Notion API with that token.
4. List the page's child blocks and look for a child database named
   `"TikTok Inspiration"`.
5. If it does not exist, create it as a child of that page with the schema below.
6. If it exists, fetch its current property schema.
7. Create any properties from the required schema that are missing; existing
   properties are left untouched.
8. Store the resulting database ID in the local `UserSettings` row
   (`notion_database_id` column) — not in an environment variable, not asked from
   you again.
9. Every subsequent sync reuses the stored database ID directly.

This is safe to run every time the app starts or syncs: finding an existing database
by name and only adding missing properties makes the whole sequence idempotent.

## Database schema (auto-created/auto-verified)

| Property name        | Type          | Notes                                              |
|-----------------------|---------------|-----------------------------------------------------|
| `Title`                | Title         | The database's required title property               |
| `TikTok URL`           | URL           | The saved TikTok link                                 |
| `Status`               | Select        | Options: `New`, `Processing`, `Processed`, `Failed`   |
| `Added`                | Created time  | Set automatically by Notion                           |
| `Creator`              | Rich text     | Original creator's handle, if known                    |
| `Topic`                | Multi-select  | Optional hint from you; back-filled by Kadro if blank |
| `Format`               | Select        | Optional hint from you; back-filled by Kadro if blank |
| `Why I saved it`       | Rich text     | Your note on why the video is interesting              |
| `My favorite part`     | Rich text     | Your note on the specific thing you liked              |
| `Processing Error`     | Rich text     | Filled in by Kadro when processing fails               |
| `Processed At`         | Date          | Filled in by Kadro when processing finishes            |
| `Already Used`         | Checkbox      | Set by Kadro when you use the "Mark as used" action -- excludes this item from future idea-generation context. Independent of `Status`; never touched by sync. |

Set a new row's `Status` to `New` when you add a link — that is the only manual step
per item.

## 4. Sync

Three equivalent ways to trigger a sync:

- UI: Inspiration page → "Sync Notion" button.
- API: `POST /api/v1/inspiration/sync-notion`.
- CLI: `python -m app.cli sync-notion` (run from `apps/api`).

Optional scheduled polling: set `NOTION_SYNC_ENABLED=true` and
`NOTION_SYNC_INTERVAL_MINUTES` (Settings page or `.env`) to run the same sync
automatically on an interval. Manual sync always works regardless of this setting.

## What the sync does

For each Notion row with `Status = New`:

1. Validate and normalize the `TikTok URL` (rejects non-TikTok hosts).
2. Check for a duplicate by normalized URL or extracted TikTok video ID; if found,
   link to the existing `InspirationItem` instead of creating a duplicate.
3. Create/update the local `InspirationItem` row, including `Topic`/`Format` hints
   and both note fields.
4. Set the Notion row's `Status` to `Processing`.
5. Run the content-resolution + analysis pipeline (see `docs/AI_PIPELINE.md`).
6. Set the Notion row's `Status` to `Processed` (with `Processed At` filled in) or
   `Failed` (with a human-readable `Processing Error` message). If `Topic`/`Format`
   were left blank, Kadro fills them in with its own classification.

Re-running a sync is safe: rows already `Processing`/`Processed`/`Failed` are skipped
unless you manually reset a row's `Status` back to `New` in Notion. Kadro never
deletes a Notion row.
