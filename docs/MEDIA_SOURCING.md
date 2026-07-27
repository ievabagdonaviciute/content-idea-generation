# Media sourcing — images and memes for an idea

On an idea's detail page, "Source images" pulls 5 real stock photos and 5 real,
captioned memes relevant to that idea, for use while editing the video. This uses
two official, licensed APIs -- never scraping, never bypassing access controls.

## Without any setup

Both `PEXELS_API_KEY` and `IMGFLIP_USERNAME`/`IMGFLIP_PASSWORD` are optional. Leave
them unset and Kadro uses deterministic fake providers
(`app/integrations/media/fake.py`) that return real, loadable placeholder images
(via picsum.photos) so the whole feature is exercisable and testable with zero
external accounts -- the images won't be topically relevant, and the "memes" are
plain placeholder images with the AI-written captions attached as metadata rather
than actually burned into the image.

## 1. Pexels (real stock photos)

1. Go to https://www.pexels.com/api/ and sign up (free).
2. Once approved (usually instant), copy your API key from
   https://www.pexels.com/api/new/.
3. Add it to `apps/api/.env`:
   ```env
   PEXELS_API_KEY=your_key_here
   ```

Free tier is generous (200 requests/hour, 20,000/month) -- far more than a personal
tool needs.

## 2. Imgflip (real meme templates + captioning)

Imgflip's captioning endpoint is authenticated with a real account's
username/password, not a separate API key -- that's how their API works, not a
Kadro design choice.

1. Create a free account at https://imgflip.com/signup.
2. Add the credentials to `apps/api/.env`:
   ```env
   IMGFLIP_USERNAME=your_username
   IMGFLIP_PASSWORD=your_password
   ```

Listing the top 100 popular templates (`get_memes`) needs no authentication;
generating a captioned image (`caption_image`) does. The free tier works but adds a
small watermark to captioned images unless you have Imgflip Pro.

## How captions are chosen

Kadro doesn't try to match a specific meme template's visual joke structure --
`app/services/idea_media.py` picks Imgflip's most popular templates and asks the
configured AI text provider (same `AI_API_KEY` used everywhere else, see
`docs/AI_PIPELINE.md`) for generic, relatable setup/punchline caption pairs about
the idea's topic, then applies each caption to a template via `caption_image`. This
keeps caption writing centralized and reusable regardless of which templates are
currently popular.

## Restart required

Like every other credential in `apps/api/.env`, `get_settings()` is cached at
process start -- restart `uvicorn` after adding these for the real providers to
take effect.
