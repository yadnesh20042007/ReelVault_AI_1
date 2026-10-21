from fastapi import APIRouter

from app.db.client import get_db
from app.errors import UpstreamFailed

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz():
    return {"status": "ok"}


@router.get("/readyz")
def readyz():
    try:
        get_db().table("source_posts").select("id").limit(1).execute()
    except Exception:
        raise UpstreamFailed("database unavailable")
    return {"status": "ready"}
