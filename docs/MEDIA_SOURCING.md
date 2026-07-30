# Media sourcing — images and memes for an idea

On an idea's detail page, "Source images" pulls 5 real stock photos and 5 real,
captioned memes for use while editing the video. This uses two official,
licensed APIs -- never scraping, never bypassing access controls.

**Requires a brief.** The button only appears once a brief has been generated
for the idea -- images/memes are planned *against that brief*, not the raw
idea, so each one has a specific place to go while editing (e.g. a beat that
says "superintelligence" gets a placement suggestion naming that exact beat,
not a generic AI-themed photo). Calling `POST /ideas/{id}/media` before a
brief exists returns 422 (`BriefRequiredError`), not a generic failure.

## How placement works

`app/services/idea_media.py` sends the AI text provider the full brief
(objective, promise, every beat, hook choices, on-screen text, closing line,
call to action) and asks for a placement *plan*
(`app/schemas/media_placement.py`): for each image, a placement description
(naming the specific beat/moment) plus a stock-photo search query; for each
meme, a placement description plus 1-2 caption lines. Only after that plan
exists does Kadro call Pexels/Imgflip -- one search per image placement, one
captioned template per meme placement. Every returned item carries its
`placement` string alongside the image/meme itself, and the idea detail page
displays it under each thumbnail.

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

## How meme templates are chosen

Kadro doesn't try to match a specific meme template's visual joke structure --
it takes Imgflip's most popular templates in order and applies the AI-written
caption for each placement via `caption_image`. Caption writing itself is
described above (tied to the brief, not the template).

## Restart required

Like every other credential in `apps/api/.env`, `get_settings()` is cached at
process start -- restart `uvicorn` after adding these for the real providers to
take effect.
