# Production Kit — Automation Pipeline

Turns a **topic idea** into a finished, narrated YouTube video — research →
script → title → video → upload — while enforcing the Production Kit safety
model (T1–T4 source tiers, no T4 claims, legal gate, private-first upload).

```
topic ──▶ /api/research ──▶ /api/script ──▶ /api/video ──▶ /api/youtube/upload
        (Claude + web      (Claude:        (Pillow slides   (YouTube Data API,
         search → T1-T3      title +         + gTTS + ffmpeg  PRIVATE first)
         claims ledger)      3-act script)   → MP4)
```

The front-end app (`docs/production-kit/`) drives this via its **🤖 Autopilot**
panel. There is a **human review gate between every stage** — exactly the one
node the Production Kit says you must never automate away.

## Why this needs a backend

The app itself is static (GitHub Pages). Video rendering (ffmpeg), the
Anthropic API key, and YouTube OAuth can't run in a browser — so this pipeline
runs on your machine (or any server you control) and the app calls it.

## Run it

```bash
cd pipeline
cp .env.example .env          # add ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001
# or: docker build -t pk-pipeline . && docker run -p 8001:8001 --env-file .env pk-pipeline
```

Then open the app, click **🤖 Autopilot**, set the backend URL to
`http://localhost:8001`, type a topic, and step through.

## YouTube upload (optional)

1. Google Cloud Console → enable **YouTube Data API v3**.
2. Create an **OAuth client ID → Desktop app**, download the JSON to
   `pipeline/client_secret.json`.
3. `POST /api/youtube/authorize` (or the app button) once — a browser opens for
   consent; the token is cached to `youtube_token.json`.
4. Uploads are **PRIVATE** and tagged as synthetic/AI media. Flip to public in
   YouTube Studio only after the Part 3 pre-publish gate clears.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/api/health` | model, web-search, youtube-auth status |
| POST | `/api/research` | `{topic, pillar?}` → defence file + gate issues |
| POST | `/api/script` | `{research}` → title + 3-act script + metadata |
| POST | `/api/video` | `{script}` → `{task_id}` (async render) |
| GET  | `/api/video/status/{id}` | progress 0–100 |
| GET  | `/api/video/file/{id}` | download the MP4 |
| POST | `/api/youtube/upload` | `{video_path,…,confirm_gate:true}` → video URL |

## Model

Defaults to `claude-opus-4-8` (set `PIPELINE_MODEL=claude-sonnet-4-6` for lower
cost). Research uses server-side web search to find real T1–T3 sources, then a
second pass structures them into the typed claims ledger.

> The pipeline will refuse to script a defence file that still contains a T4
> claim or a below-T1 claim worded as fact, and will refuse to upload unless
> `confirm_gate=true`. That enforcement is the point — automate the assembly
> line, never Part 1's judgment.
