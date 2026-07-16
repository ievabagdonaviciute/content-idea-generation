# Lithuanian Generation Guide — Kadro

Lithuanian is a first-class product requirement. This document defines the style
contract that every prompt in `apps/api/app/ai/prompts/` must follow, and what
reviewers/tests should check for.

## Defaults

- `UserSettings.default_output_language = "lt"`. Every generation endpoint accepts an
  optional `output_language` override (`lt` default, `en` alternative); when omitted,
  the user setting applies.
- All creator-facing generated fields (idea title/concept/hooks/outline, brief
  fields, script lines, captions, CTAs, similarity-warning text, profile summary
  sentences) are generated directly in the target language by the model — not
  produced in English and machine-translated. Translation-then-localization produces
  the stiff, literal phrasing this guide explicitly forbids.

## Voice contract (baked into every Lithuanian prompt)

The shared prompt fragment `LT_VOICE_GUIDE` (`apps/api/app/ai/prompts/voice.py`)
instructs the model to:

- sound like a young Lithuanian technology creator talking to camera, not a marketing
  department;
- use correct Lithuanian diacritics (ą č ę ė į š ų ū ž) everywhere — never strip them;
- prefer natural word order and idiom over literal English calques (e.g. not
  *"Tai yra labai svarbu žinoti"* as a stock opener — Lithuanian creators start with
  the hook, not a meta-statement);
- keep English technical terms creators actually use in Lithuanian tech content
  as-is (e.g. "AI", "startup", "hardware", "prompt", "open source") rather than
  forcing an awkward Lithuanian neologism, but write everything else in Lithuanian —
  no random code-switching mid-sentence for non-technical words;
- avoid corporate/marketing register ("pasinerkite į", "atraskite naujus horizontus")
  and avoid over-slangy youth-speak that would sound try-hard;
- vary sentence length — short punchy sentences mixed with longer explanatory ones,
  because a spoken script read in one cadence sounds robotic;
- support both an informative register (explainer/news-recap content) and a casual
  register (GRWM/personal-story content), chosen by the requested content format or
  script mode.

## Format-specific guidance

`apps/api/app/ai/prompts/script_modes.py` maps each script mode to Lithuanian
structural guidance, e.g.:

- `polished_educational_explainer`: hook as a question or a surprising claim, clear
  throughline, one main idea per beat, no filler rhetorical questions stacked
  back-to-back.
- `grwm_story`: casual, present-tense, first person, routine actions interleaved with
  the story beats, contractions/spoken particles ("na", "tai va") used sparingly.
- `tech_news_recap`: leads with what happened, then why it matters, ends with a
  one-line opinion, not a generic "let me know what you think" close.
- `comment_response`: quotes/paraphrases the comment briefly, then answers directly.
- `personal_engineering_story`: first person, concrete and specific, explicitly
  labels any placeholder needed for a personal detail the model cannot know
  (e.g. `[ĮRAŠYK: kurso pavadinimas]`) instead of inventing one.

## Hard constraints enforced in prompts and validated where practical

- Never fabricate a personal experience/anecdote as if it happened — placeholders
  only.
- Never repeat the hook verbatim as the conclusion.
- At least three hook options per idea, and they must not share the same syntactic
  template (checked by a lightweight heuristic in
  `apps/api/tests/test_lithuanian_output.py` — hooks must differ in opening word/
  structure, not just wording).
- Scripts separate spoken text from editing directions (`spoken_lines` vs.
  `editing_notes` in `GeneratedScript`) so the spoken track never accidentally
  contains a bracketed instruction.

## Output-language setting

`app/services/idea_generation.py`, `brief_generation.py`, and `script_generation.py`
all thread `output_language` through to prompt selection: the same prompt templates
exist in an LT and EN variant (`apps/api/app/ai/prompts/lt/` and
`apps/api/app/ai/prompts/en/`) so an English request does not get an
English-instructions-producing-Lithuanian-text mismatch.

## Fake provider behavior

`FakeTextGenerationProvider` produces valid, schema-conforming Lithuanian placeholder
text (real diacritics, varied hook templates) when `output_language="lt"`, and English
placeholder text for `"en"`, so language-selection tests do not require a live model.
