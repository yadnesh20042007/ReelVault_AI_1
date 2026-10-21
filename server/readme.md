# ReelVault AI — backend

Paste an Instagram / YouTube / TikTok link. The API returns the transcript (shallow cook). You can then start a deep cook: Gemini classifies and extracts fields, Tavily searches the web, and you get a verdict plus a sourced briefing.

## What you need (API keys)

Create `server/.env` from `.env.example`. Four services:

| Env var | Where to get it | Used for |
|---|---|---|
| `SUPABASE_URL` | [Supabase](https://supabase.com) → Project Settings → API | Database + Auth |
| `SUPABASE_ANON_KEY` | same page (anon / publishable) | Signup, login, token check |
| `SUPABASE_SERVICE_ROLE_KEY` | same page (service_role) — **server only, never in a client** | Postgres reads/writes |
| `SOCIALKIT_API_KEY` | [SocialKit](https://socialkit.dev) | Reel transcripts |
| `TAVILY_API_KEY` | [Tavily](https://tavily.com) | Web search + page extract (deep cook) |
| `GEMINI_API_KEY` (or `_2`, `_3`) | [Google AI Studio](https://aistudio.google.com/apikey) | Classify, extract, verify, research (supports multiple keys for rotation & failover) |

### One-time Supabase setup

1. New project → **SQL Editor** → run every file in `supabase/migrations/`, in numeric order (`0001_init.sql`, `0002_productivity_shelf.sql`, then `0003_link_vault_entries.sql`).
2. **Authentication → Providers → Email** ON.
3. For local testing, turn **email confirmation OFF** so signup returns tokens immediately.

## Run

```bash
cd server
copy .env.example .env
# fill the keys in .env
pip install -e .
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/healthz

Shallow cook can take up to ~60s (SocialKit). Deep cook is async — poll until `done` / `not_opportunity` / `failed`.

---

## Routes and sample payloads

Base URL: `http://127.0.0.1:8000`

Use `Authorization: Bearer <access_token>` on every `/v1/reels/*` route and on logout / me.

### Health (public)

**`GET /healthz`** — process is up

```bash
curl http://127.0.0.1:8000/healthz
```

Response: `{ "status": "ok" }`

**`GET /readyz`** — can talk to Supabase

```bash
curl http://127.0.0.1:8000/readyz
```

Response: `{ "status": "ready" }` (or `502` if DB is down)

---

### Auth (public except logout / me)

**`POST /v1/auth/signup`**

```json
{
  "email": "you@example.com",
  "password": "a-strong-password"
}
```

```bash
curl -X POST http://127.0.0.1:8000/v1/auth/signup -H "Content-Type: application/json" -d "{\"email\":\"you@example.com\",\"password\":\"a-strong-password\"}"
```

201 example (confirmation off):

```json
{
  "user": { "id": "uuid", "email": "you@example.com" },
  "confirmation_required": false,
  "session": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": { "id": "uuid", "email": "you@example.com" }
  }
}
```

If confirmation is ON: `session` is `null` and you must confirm email before login.

**`POST /v1/auth/login`**

```json
{
  "email": "you@example.com",
  "password": "a-strong-password"
}
```

```bash
curl -s -X POST http://127.0.0.1:8000/v1/auth/login -H "Content-Type: application/json" -d "{\"email\":\"you@example.com\",\"password\":\"a-strong-password\"}"
```

200:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { "id": "uuid", "email": "you@example.com" }
}
```

Save `access_token`. Wrong password → `401` `{ "error": { "code": "invalid_credentials", "message": "Invalid email or password." } }`

**`POST /v1/auth/refresh`**

```json
{ "refresh_token": "<refresh_token>" }
```

Returns a new `TokenOut` (store the new refresh token; it rotates).

**`GET /v1/auth/me`**

```bash
curl http://127.0.0.1:8000/v1/auth/me -H "Authorization: Bearer ACCESS_TOKEN"
```

```json
{ "id": "uuid", "email": "you@example.com" }
```

**`POST /v1/auth/logout`**

```json
{ "all_devices": false }
```

```bash
curl -X POST http://127.0.0.1:8000/v1/auth/logout -H "Authorization: Bearer ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"all_devices\":false}"
```

204 empty body.

---

### Reels (Bearer required)

**`POST /v1/reels`** — shallow cook (transcript)

```json
{ "url": "https://www.instagram.com/reel/XXXXXXXXXXX/" }
```

Also valid:

- `https://www.youtube.com/shorts/abcdefghijk`
- `https://www.youtube.com/watch?v=abcdefghijk`
- `https://youtu.be/abcdefghijk`
- `https://www.tiktok.com/@user/video/7522711492140059912`

```bash
curl -X POST http://127.0.0.1:8000/v1/reels -H "Authorization: Bearer ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"url\":\"https://www.instagram.com/reel/XXXXXXXXXXX/\"}"
```

200:

```json
{
  "reel_id": 1,
  "platform": "instagram",
  "url": "https://www.instagram.com/reel/XXXXXXXXXXX/",
  "transcript": "...verbatim speech...",
  "caption": null,
  "language": null,
  "cached": false,
  "created_at": "2026-10-04T17:00:00+00:00"
}
```

Same URL again → same `reel_id`, `cached: true`, no SocialKit call.

Errors: `422 invalid_url` (not IG/YT/TikTok), `422 no_content` (silent reel, no caption), `429 rate_limited` (50 new reels / 24h), `502 upstream_failed`.

**`GET /v1/reels?limit=20&offset=0`** — history

```bash
curl "http://127.0.0.1:8000/v1/reels?limit=20&offset=0" -H "Authorization: Bearer ACCESS_TOKEN"
```

```json
[
  {
    "reel_id": 1,
    "platform": "instagram",
    "url": "https://www.instagram.com/reel/XXXXXXXXXXX/",
    "transcript_preview": "first 200 chars...",
    "created_at": "2026-10-04T17:00:00+00:00",
    "deep_cook_status": null
  }
]
```

**`GET /v1/reels/{reel_id}`** — one reel + latest deep cook

```bash
curl http://127.0.0.1:8000/v1/reels/1 -H "Authorization: Bearer ACCESS_TOKEN"
```

Someone else's id (or missing) → `404` (never 403).

**`DELETE /v1/reels/{reel_id}`** — removes your history row (and its deep cooks). Shared transcript cache stays.

```bash
curl -X DELETE http://127.0.0.1:8000/v1/reels/1 -H "Authorization: Bearer ACCESS_TOKEN"
```

204.

**`POST /v1/reels/{reel_id}/deep-cook`** — start Gemini + Tavily job (no body)

```bash
curl -X POST http://127.0.0.1:8000/v1/reels/1/deep-cook -H "Authorization: Bearer ACCESS_TOKEN"
```

202:

```json
{
  "id": 1,
  "status": "queued",
  "error_code": null,
  "classification": null,
  "extracted": null,
  "verification": null,
  "report": null,
  "created_at": "2026-10-04T17:01:00+00:00",
  "finished_at": null
}
```

If a job is already running for that reel, you get that row instead of a duplicate. Limit: 10 deep cooks / user / 24h → `429`.

**`GET /v1/reels/{reel_id}/deep-cook`** — poll every 2–3s

```bash
curl http://127.0.0.1:8000/v1/reels/1/deep-cook -H "Authorization: Bearer ACCESS_TOKEN"
```

Stop when `status` is `done`, `not_opportunity`, or `failed`.

Statuses: `queued` → `classifying` → `extracting` → `verifying` → `researching` → `done`  
(or stop at `not_opportunity` after classify).

When done, `verification.verdict` is one of: `official_confirmed`, `found_unofficial`, `conflicting`, `not_found`, `suspicious`.

---

## PowerShell one-shot (Windows)

```powershell
$base = "http://127.0.0.1:8000"
$login = Invoke-RestMethod -Method POST "$base/v1/auth/login" -ContentType "application/json" -Body '{"email":"you@example.com","password":"a-strong-password"}'
$h = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Method POST "$base/v1/reels" -Headers $h -ContentType "application/json" -Body '{"url":"https://www.instagram.com/reel/XXXXXXXXXXX/"}'
```

---

## How the pipeline works

```
URL ──► allowlist (IG / YT / TikTok only)
      ──► cache hit? return transcript
      ──► else SocialKit transcript ──► store source_posts + user_reels

Deep cook (background):
  Gemini Flash  classify  ──► not an opportunity? stop
  Gemini Flash  extract   ──► drop any field whose quote is not in the transcript
  Tavily search/extract   ──► Verdict Guard (code, not the model) decides the badge
  Gemini + Tavily         ──► sourced report (skipped if verdict is not_found)
```

Gemini never talks to the database. Only `repo.py` and the two orchestrators (`shallow_cook`, `run_deep_cook`) do.

## Error envelope

```json
{ "error": { "code": "invalid_url", "message": "Only Instagram, YouTube and TikTok video links are supported." } }
```
