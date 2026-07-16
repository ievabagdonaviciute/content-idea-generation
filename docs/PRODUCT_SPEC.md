# Product Specification — Kadro

## What Kadro is

Kadro is a single-user, personal TikTok content-planning platform. It analyzes the
posts already published on one TikTok account, learns that creator's recurring
subjects, formats, hooks, and tone, ingests inspiration links saved to a Notion
database, and generates original Lithuanian-language TikTok ideas, briefs, and
scripts that fit the creator's identity while stating how each idea was inspired and
how it differs from its source.

The temporary project name `Kadro` lives in exactly one place:
`apps/api/app/core/config.py` (`settings.project_name`) and
`apps/web/lib/config.ts` (`APP_NAME`). Renaming the product means editing those two
constants.

## Who it is for

One creator: `ieva.bagdonaviciute` on TikTok (configurable, not hard-coded — see
`UserSettings.tiktok_username`). This is not a multi-tenant SaaS product. There is no
public sign-up flow. Authentication is intentionally out of scope for the MVP, but the
codebase is structured (settings-backed, no hard-coded user context) so a real login
system could be added without a rewrite.

## Core workflows

1. **Analyze my TikTok account** — sync posts through an `OwnContentProvider`
   adapter (mock adapter for local dev, TikTok Login Kit + Display API scaffold for
   production), run them through the analysis pipeline, and build a content profile.
2. **Notion inspiration inbox** — poll or manually sync a Notion database of saved
   TikTok links, normalize and deduplicate URLs, and track each item through
   `New -> Processing -> Processed/Failed`.
3. **Resolve inspiration content** — a tiered resolver (oEmbed metadata -> optional
   authorized media access -> metadata-only fallback) that never fabricates a
   transcript or visual analysis it could not obtain.
4. **Analyze content** — an explicit, independently testable pipeline that turns raw
   video/metadata into a structured, validated `ContentAnalysis` record.
5. **Build a content profile** — a derived, versioned snapshot of the creator's
   pillars, formats, hooks, tone distribution, and content gaps, with confidence and
   sample-size tracking so tentative conclusions are distinguishable from strongly
   supported ones.
6. **Generate ideas** — retrieval-augmented idea generation with a configurable
   alignment/format-stretch/experimental mixture, similarity checks against existing
   posts, and an explicit inspiration-pattern / originality-note pair per idea.
7. **Turn an idea into a brief and script** — Lithuanian production brief (beat by
   beat) and a full spoken script in one of several script modes.
8. **Collect feedback** — Love / Maybe / Not for me / Already covered, plus free text,
   stored and used as retrieval context for future generations (no opaque retraining).

## Non-goals for the MVP

- No public multi-user auth, billing, or admin panel.
- No background worker infrastructure (Redis/Celery/Kafka) — a database-backed job
  table plus synchronous/CLI execution stands in for it.
- No unofficial TikTok scraping, CAPTCHA bypass, or anti-bot evasion of any kind.
- No guarantee that full video media is downloadable — the system is designed to stay
  useful in `metadata_only` mode.
- No fine-tuning or opaque ML retraining on feedback; feedback is structured retrieval
  context only.

## Content formats recognized

Formats are rows in a `content_formats` reference table (seeded, not a hard-coded
enum), so new formats can be added without a schema migration touching every table
that references one. The seed set covers all formats listed in the brief (edited tech
explainer, casual talking-head, GRWM story, personal experience/opinion, tech news
recap, educational history explainer, comment response, vlog, voice-over + B-roll,
screen recording/demo, list/ranking, reaction, myth-vs-fact, university/engineering
life story, interview-style answer, trend adapted to an educational subject). See
`docs/DATA_MODEL.md`.

## Inspiration vs. imitation

The analysis schema separates *topic* from *hook mechanism*, *narrative structure*,
*pacing*, *visual presentation*, *emotional angle*, *audience promise*, and
*call-to-action pattern* specifically so idea generation can borrow structural
patterns without copying wording. The idea-generation prompt (see
`docs/AI_PIPELINE.md`) explicitly forbids reproducing another creator's exact hook
text, jokes, or examples, and every generated idea must carry an `inspiration_pattern`
and an `originality_note` field explaining the adaptation and the difference from the
source.

## Language

Lithuanian is the default output language for all creator-facing generated content
(ideas, hooks, briefs, scripts, captions, CTAs, explanations, similarity warnings,
profile summaries). English is available as a per-request/per-setting alternative.
See `docs/LITHUANIAN_GENERATION_GUIDE.md`.
