import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, reels
from app.config import get_settings
from app.db import repo
from app.errors import register_error_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="ReelVault API", version="0.3.0")
cors_origins = get_settings().cors_origins
allow_origin_regex = None if ("*" in cors_origins) else r"^https://.*\.vercel\.app$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=allow_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)
app.include_router(health.router)
app.include_router(auth.router, prefix="/v1")
app.include_router(reels.router, prefix="/v1")


@app.on_event("startup")
def close_interrupted_deep_cooks() -> None:
    """Prevent stale in-process jobs from leaving browser polling loops behind."""
    try:
        count = repo.fail_interrupted_deep_cooks()
        if count:
            logging.getLogger("deep_cook").warning("marked %s interrupted deep-cook job(s) as failed", count)
    except Exception:
        # The API can still serve authentication and existing reels while the
        # database connection is temporarily unavailable at startup.
        logging.getLogger("deep_cook").exception("could not close interrupted deep-cook jobs")
