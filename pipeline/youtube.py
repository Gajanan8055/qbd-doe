"""Stage 4 of the pipeline: upload the MP4 to YouTube (Data API v3).

Auth is a one-time OAuth consent flow on the machine running this server. The
resulting token is cached so later uploads need no interaction. Videos are
uploaded PRIVATE by default — the Production Kit pre-publish gate must clear
before anything goes public.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from config import YOUTUBE_CLIENT_SECRETS, YOUTUBE_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    token_path = Path(YOUTUBE_TOKEN_FILE)
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())
        return creds
    if not Path(YOUTUBE_CLIENT_SECRETS).exists():
        raise FileNotFoundError(
            f"YouTube client secrets not found at {YOUTUBE_CLIENT_SECRETS}. "
            "Download an OAuth 'Desktop app' client from Google Cloud Console."
        )
    flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRETS, SCOPES)
    creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json())
    return creds


def is_authorized() -> bool:
    try:
        from google.oauth2.credentials import Credentials
        token_path = Path(YOUTUBE_TOKEN_FILE)
        if not token_path.exists():
            return False
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        return bool(creds and (creds.valid or creds.refresh_token))
    except Exception:
        return False


def authorize() -> bool:
    """Run the one-time consent flow (opens a browser on this machine)."""
    _credentials()
    return True


def upload(
    video_path: str,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    privacy: str = "private",
    category_id: str = "25",  # News & Politics
) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    if not Path(video_path).exists():
        raise FileNotFoundError(video_path)

    youtube = build("youtube", "v3", credentials=_credentials())
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": (tags or [])[:15],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            # YouTube altered/synthetic-content disclosure for AI-generated media.
            "containsSyntheticMedia": True,
        },
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()
    vid = response["id"]
    return {"video_id": vid, "url": f"https://youtu.be/{vid}", "privacy": privacy}
