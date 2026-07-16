# AI Pipeline — Kadro

## Provider interfaces

Defined in `apps/api/app/ai/base.py` as `Protocol`s, so the rest of the app never
imports a vendor SDK directly:

```python
class TranscriptionProvider(Protocol):
    async def transcribe(self, audio_path: Path) -> TranscriptionResult: ...

class VisionAnalysisProvider(Protocol):
    async def describe_frames(self, frame_paths: list[Path]) -> VisualDescription: ...

class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

class TextGenerationProvider(Protocol):
    async def generate_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel: ...
```

Two implementations of each:

- `Fake*` (`apps/api/app/ai/fake_providers.py`) — deterministic, seeded from a hash of
  the input so the same input always analyzes the same way. Used by default (no
  `AI_API_KEY` configured) and in all tests. Never calls the network.
- `OpenAICompatibleProvider` (`apps/api/app/ai/openai_compatible.py`) — calls
  `AI_BASE_URL` (defaults to `https://api.openai.com/v1`) with `AI_API_KEY` via
  `httpx.AsyncClient`, using model names from `AI_TEXT_MODEL`, `AI_VISION_MODEL`,
  `AI_TRANSCRIPTION_MODEL`, `AI_EMBEDDING_MODEL`. Domain code never references a model
  name literal.

Provider selection happens once, in `app/ai/factory.py`, based on whether
`settings.ai_api_key` is set. Everything downstream depends on the `Protocol`, not the
concrete class (constructor injection via FastAPI `Depends`).

## Pipeline stages

`apps/api/app/pipelines/analysis_pipeline.py` implements each stage as a small,
independently testable function, composed by `run_analysis_pipeline`:

```text
ingest_source            -> pulls the raw SourceVideo/InspirationItem + any Notion notes
normalize_metadata       -> canonical URL, video id, caption, creator, posted_at
acquire_permitted_content-> calls InspirationContentResolver / own-content media path;
                             sets `availability`; never guesses
extract_audio            -> ffmpeg, only if full_media and a video file is present
transcribe               -> TranscriptionProvider, only if audio was extracted;
                             records detected language (lt/en/mixed/unknown)
sample_frames            -> deterministic evenly-spaced frame extraction via ffmpeg,
                             capped at a configurable frame count, only if full_media
analyze_content           -> TextGenerationProvider (+ VisionAnalysisProvider if frames
                             exist) produces a ContentAnalysis Pydantic model
store_structured_features-> persist ContentAnalysis row
create_embeddings        -> EmbeddingProvider over topic+hook+structure text
mark_processing_status   -> pending -> processing -> completed/failed on the owning
                             OwnPost/InspirationItem and the ProcessingJob row
```

Each stage takes and returns plain dataclasses/Pydantic models — no stage reaches into
another stage's internals, and each has a focused unit test in
`apps/api/tests/test_analysis_pipeline.py`.

When only text (caption/notes) is available, `visual_analysis_available` is set to
`false` and visual-only fields (`presentation_style` visual entries) are left as
`"unknown"` rather than guessed — enforced by the Pydantic validator on
`ContentAnalysis`.

## Structured output validation

`ContentAnalysis` (in `apps/api/app/schemas/content_analysis.py`) is a Pydantic v2
model matching the JSON shape in the brief, with field-level enums/constraints
(`confidence: float` in `[0,1]`, `personal_story_level`/`educational_level` in
`[0,1]`, closed literal sets for `editing_intensity`/`estimated_pacing`, etc.).

`app/ai/json_generation.py` wraps every structured-output call:

1. Ask `TextGenerationProvider.generate_json(prompt, ContentAnalysis)`.
2. Validate with `ContentAnalysis.model_validate`.
3. On `ValidationError`, retry up to `AI_JSON_MAX_REPAIR_ATTEMPTS` (default 2) with a
   repair prompt that includes the validation error text.
4. If still invalid, log the failure (structured log, not raised as a 500 with a raw
   traceback to the client) and mark the `ProcessingJob`/analysis row `failed` with the
   validation error message. A malformed response is never written as a successful
   `ContentAnalysis`.

## Embeddings and similarity

`EmbeddingProvider.embed` runs over a compact representation of each analysis
(`primary_topic + secondary_topics + hook.text + audience_promise`), stored in
`ContentAnalysis.embedding` via the dialect-aware `Vector` type (see
`docs/ARCHITECTURE.md`). `app/services/similarity.py` computes cosine similarity —
`ORDER BY embedding <=> :query` on Postgres/pgvector, an in-Python cosine loop over
already-fetched rows on SQLite — and maps a similarity score to a category:

| similarity score        | category            |
|--------------------------|----------------------|
| below `related_low`      | `new`                |
| `related_low`..`related_high` | `related_but_distinct` or `follow_up` (by topic+claim overlap) |
| above `too_similar_threshold` | `too_similar`  |

Thresholds are configurable in `UserSettings` (`similarity_threshold` plus derived
bands). Topic-only overlap with a different format/angle is never auto-rejected — see
`app/services/similarity.py::categorize`.

## Idea generation

`app/services/idea_generation.py`:

1. Pull retrieval context: latest `ContentProfileSnapshot`, top-K own posts by
   embedding similarity to the requested pillar/format/instructions, recent
   unarchived `InspirationItem`s with analysis, recently-underused formats/topics
   from the profile, and recent `IdeaFeedback` (as short textual context, not
   retraining).
2. Decide a novelty bucket per requested idea using the configurable mixture
   (`aligned_ratio` / `stretch_ratio` / `experimental_ratio`, default 60/25/15,
   validated to sum to 1.0).
3. Build one Lithuanian-instruction prompt per idea including the bucket, retrieved
   context (summarized, not the whole database), and any user-supplied instructions
   or excluded subjects.
4. Call `TextGenerationProvider.generate_json` against the `ContentIdea` schema,
   validate, and run it through the similarity checker before returning it.
5. Persist `ContentIdea` + `IdeaSource` rows recording exactly which posts/inspiration
   items were retrieved as context for that idea.

Idea generation never sends the entire database to the model — only the retrieved,
summarized context described above.

## Briefs and scripts

`app/services/brief_generation.py` and `app/services/script_generation.py` follow the
same generate-and-validate pattern against `GeneratedBrief`/`GeneratedScript` schemas.
Script generation accepts a `mode` (`polished_explainer`, `casual_talking_head`,
`grwm_story`, `news_recap`, `comment_response`, `personal_story`) that changes the
prompt's structural guidance (see `docs/LITHUANIAN_GENERATION_GUIDE.md`).
