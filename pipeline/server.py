"""Production Kit pipeline API.

Endpoints (topic -> research -> script -> video -> YouTube), with the Production
Kit safety model enforced server-side: T4 claims and below-T1 'fact' wording are
flagged, and nothing uploads until the caller passes the gate explicitly.

Run:  uvicorn server:app --host 0.0.0.0 --port 8001
"""
from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import config
from config import MODEL, OUTPUT_DIR, ResearchResult, ScriptResult, gate_research

app = FastAPI(title="Production Kit Pipeline", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task registry for long-running video jobs.
_tasks: Dict[str, dict] = {}


# ── Request/response models ────────────────────────────────────────────────
class ResearchReq(BaseModel):
    topic: str
    pillar: Optional[str] = None


class ResearchResp(BaseModel):
    research: ResearchResult
    issues: List[str]
    ready: bool


class ScriptReq(BaseModel):
    research: ResearchResult


class VideoReq(BaseModel):
    script: ScriptResult


class UploadReq(BaseModel):
    video_path: str
    title: str
    description: str = ""
    tags: List[str] = []
    privacy: str = "private"
    confirm_gate: bool = False


# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    yt = False
    try:
        import youtube
        yt = youtube.is_authorized()
    except Exception:
        pass
    return {"ok": True, "model": MODEL, "web_search": config.WEB_SEARCH, "youtube_authorized": yt}


# ── Stage 1: research ──────────────────────────────────────────────────────
@app.post("/api/research", response_model=ResearchResp)
def do_research(req: ResearchReq):
    if not req.topic.strip():
        raise HTTPException(400, "topic is required")
    import research as research_mod
    try:
        r = research_mod.research(req.topic, req.pillar)
    except Exception as e:
        raise HTTPException(502, f"research failed: {e}")
    issues = gate_research(r)
    return ResearchResp(research=r, issues=issues, ready=not issues)


# ── Stage 2: script ────────────────────────────────────────────────────────
@app.post("/api/script", response_model=ScriptResult)
def do_script(req: ScriptReq):
    issues = gate_research(req.research)
    if issues:
        raise HTTPException(400, f"Part 1 not clean — fix before scripting: {issues}")
    import script_gen
    try:
        return script_gen.generate_script(req.research)
    except Exception as e:
        raise HTTPException(502, f"script generation failed: {e}")


# ── Stage 3: video (async) ─────────────────────────────────────────────────
def _run_video(task_id: str, script: ScriptResult):
    def progress(p: int, msg: str):
        _tasks[task_id].update(progress=p, message=msg)

    try:
        import video_gen
        out = video_gen.build_video(script, OUTPUT_DIR, progress)
        _tasks[task_id].update(status="done", progress=100, message="Video ready",
                               video_path=str(out))
    except Exception as e:
        _tasks[task_id].update(status="error", message=f"{e}")


@app.post("/api/video")
def start_video(req: VideoReq):
    task_id = uuid.uuid4().hex[:12]
    _tasks[task_id] = {"status": "running", "progress": 0, "message": "Starting"}
    threading.Thread(target=_run_video, args=(task_id, req.script), daemon=True).start()
    return {"task_id": task_id}


@app.get("/api/video/status/{task_id}")
def video_status(task_id: str):
    t = _tasks.get(task_id)
    if not t:
        raise HTTPException(404, "unknown task")
    return t


@app.get("/api/video/file/{task_id}")
def video_file(task_id: str):
    t = _tasks.get(task_id)
    if not t or t.get("status") != "done":
        raise HTTPException(404, "video not ready")
    return FileResponse(t["video_path"], media_type="video/mp4",
                        filename=Path(t["video_path"]).name)


# ── Stage 4: YouTube ───────────────────────────────────────────────────────
@app.get("/api/youtube/status")
def youtube_status():
    import youtube
    return {"authorized": youtube.is_authorized()}


@app.post("/api/youtube/authorize")
def youtube_authorize():
    """One-time consent flow (opens a browser on the server machine)."""
    import youtube
    try:
        youtube.authorize()
        return {"authorized": True}
    except Exception as e:
        raise HTTPException(400, f"authorization failed: {e}")


@app.post("/api/youtube/upload")
def youtube_upload(req: UploadReq):
    if not req.confirm_gate:
        raise HTTPException(
            400,
            "Pre-publish gate not confirmed. Set confirm_gate=true only after the "
            "Part 3 checklist passes. (Uploads default to PRIVATE regardless.)",
        )
    import youtube
    try:
        return youtube.upload(
            req.video_path, req.title, req.description, req.tags, req.privacy
        )
    except Exception as e:
        raise HTTPException(502, f"upload failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=config.HOST, port=config.PORT, reload=False)
