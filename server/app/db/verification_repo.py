import json
import logging
import os
from pathlib import Path
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.db.client import get_db
from app.errors import AppError

log = logging.getLogger("verification_repo")

_DEV_STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / ".dev_storage"
_DEV_STORAGE_FILE = _DEV_STORAGE_DIR / "verification_store.json"


class PersistentFallbackStore:
    """Thread-safe, disk-backed fallback store used in development mode.
    
    Persists verification runs and stages to a local JSON file so that state
    survives FastAPI process restarts until migration 0004_verification_stages.sql
    is applied to the remote Supabase project by the project owner.
    Explicitly marked as development-only.
    """

    def __init__(self, storage_file: Path | None = None):
        self._lock = threading.Lock()
        self._storage_file = storage_file or _DEV_STORAGE_FILE
        self._runs: dict[str, dict[str, Any]] = {}
        self._stages: dict[str, list[dict[str, Any]]] = {}
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        with self._lock:
            if not self._storage_file.exists():
                return
            try:
                data = json.loads(self._storage_file.read_text(encoding="utf-8"))
                self._runs = data.get("runs", {})
                self._stages = data.get("stages", {})
            except Exception as exc:
                log.warning("Could not read local verification store (%s). Initializing fresh state.", exc)

    def _flush_to_disk(self) -> None:
        try:
            self._storage_file.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self._storage_file.with_suffix(".tmp")
            content = json.dumps({"runs": self._runs, "stages": self._stages}, indent=2)
            temp_path.write_text(content, encoding="utf-8")
            if os.name == "nt" and self._storage_file.exists():
                self._storage_file.unlink()
            temp_path.replace(self._storage_file)
        except Exception as exc:
            log.warning("Could not flush local verification store to disk: %s", exc)

    def create_run(self, user_id: str, raw_input: str, input_type: str = "rvpack", user_reel_id: int | None = None) -> dict:
        with self._lock:
            run_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            run = {
                "id": run_id,
                "user_id": user_id,
                "user_reel_id": user_reel_id,
                "input_type": input_type,
                "raw_input": raw_input,
                "status": "in_progress",
                "current_stage": "extracted",
                "error_message": None,
                "persistence_backend": "development_file_fallback",
                "created_at": now,
                "updated_at": now,
            }
            self._runs[run_id] = run
            self._stages[run_id] = []
            self._flush_to_disk()
            return dict(run)

    def get_run(self, run_id: str, user_id: str | None = None) -> dict | None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return None
            if user_id and str(run.get("user_id")) != str(user_id):
                return None
            return dict(run)

    def update_run(self, run_id: str, **fields) -> dict | None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return None
            fields["updated_at"] = datetime.now(timezone.utc).isoformat()
            run.update(fields)
            self._flush_to_disk()
            return dict(run)

    def save_stage(self, run_id: str, stage_name: str, stage_order: int, payload: dict, status: str = "completed") -> dict:
        with self._lock:
            stage_list = self._stages.setdefault(run_id, [])
            # Prevent duplicate records for the same stage (enforce idempotency)
            for s in stage_list:
                if s["stage_name"] == stage_name or s["stage_order"] == stage_order:
                    return dict(s)

            stage_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            record = {
                "id": stage_id,
                "run_id": run_id,
                "stage_name": stage_name,
                "stage_order": stage_order,
                "status": status,
                "payload": payload,
                "created_at": now,
            }
            stage_list.append(record)
            stage_list.sort(key=lambda s: s["stage_order"])
            self._flush_to_disk()
            return dict(record)

    def get_stage(self, run_id: str, stage_name: str) -> dict | None:
        with self._lock:
            for s in self._stages.get(run_id, []):
                if s["stage_name"] == stage_name:
                    return dict(s)
            return None

    def list_stages(self, run_id: str) -> list[dict]:
        with self._lock:
            items = self._stages.get(run_id, [])
            return [dict(s) for s in sorted(items, key=lambda x: x["stage_order"])]

    def reset(self) -> None:
        with self._lock:
            self._runs = {}
            self._stages = {}
            if self._storage_file.exists():
                try:
                    self._storage_file.unlink()
                except Exception:
                    pass


_fallback_store = PersistentFallbackStore()
_supabase_tables_available: bool | None = None
_custom_db_client: Any = None


def set_custom_db_client(client: Any = None) -> None:
    """Allow test suites to inject a mocked Supabase client."""
    global _custom_db_client, _supabase_tables_available
    _custom_db_client = client
    _supabase_tables_available = None


def get_active_db() -> Any:
    if _custom_db_client is not None:
        return _custom_db_client
    return get_db()


def is_durable_storage() -> bool:
    """Returns True if persisted to real Supabase tables; False if using dev fallback store."""
    return bool(_check_supabase_tables())


def get_storage_backend() -> str:
    """Returns 'supabase' or 'development_file_fallback'."""
    return "supabase" if _check_supabase_tables() else "development_file_fallback"


def _check_supabase_tables() -> bool:
    global _supabase_tables_available
    if _supabase_tables_available is not None:
        return _supabase_tables_available

    try:
        db = get_active_db()
        db.table("verification_runs").select("id").limit(1).execute()
        _supabase_tables_available = True
        log.info("[SUPABASE] Supabase verification tables are active and connected.")
    except Exception as exc:
        _supabase_tables_available = False
        settings = get_settings()
        if settings.app_env == "production":
            log.error(
                "[PRODUCTION CRITICAL] Supabase verification tables missing from schema: %s. "
                "Migration 0004_verification_stages.sql must be applied by project owner.",
                exc,
            )
        else:
            log.warning(
                "[DEV FALLBACK] Supabase verification tables not yet active (%s). "
                "Using persistent development store at %s pending migration 0004_verification_stages.sql.",
                exc,
                _DEV_STORAGE_FILE,
            )
    return _supabase_tables_available


def create_run(user_id: str, raw_input: str, input_type: str = "rvpack", user_reel_id: int | None = None) -> dict:
    if _check_supabase_tables():
        try:
            db = get_active_db()
            payload = {
                "user_id": user_id,
                "raw_input": raw_input,
                "input_type": input_type,
                "status": "in_progress",
                "current_stage": "extracted",
            }
            if user_reel_id:
                payload["user_reel_id"] = user_reel_id
            res = db.table("verification_runs").insert(payload).execute()
            if res.data:
                run_data = res.data[0]
                run_data["persistence_backend"] = "supabase"
                return run_data
        except Exception as exc:
            log.warning("Supabase insert verification_runs failed: %s", exc)
            if get_settings().app_env == "production":
                raise AppError(
                    f"Durable database persistence failed in production: {exc}",
                    status=500,
                    code="database_persistence_failed",
                )

    if get_settings().app_env == "production":
        raise AppError(
            "Supabase verification tables not found in production environment. "
            "Please review and apply migration 0004_verification_stages.sql.",
            status=500,
            code="database_schema_missing",
        )

    return _fallback_store.create_run(user_id, raw_input, input_type, user_reel_id)


def get_run(run_id: str, user_id: str | None = None) -> dict | None:
    if _check_supabase_tables():
        try:
            db = get_active_db()
            query = db.table("verification_runs").select("*").eq("id", run_id)
            if user_id:
                query = query.eq("user_id", user_id)
            res = query.limit(1).execute()
            if res.data:
                run_data = res.data[0]
                run_data["persistence_backend"] = "supabase"
                return run_data
            # If query succeeded but returned no rows, row belongs to another user or doesn't exist
            return None
        except Exception as exc:
            log.warning("Supabase get verification_runs failed: %s", exc)
            if get_settings().app_env == "production":
                raise AppError(f"Database query failed: {exc}", status=500, code="database_error")

    return _fallback_store.get_run(run_id, user_id)


def update_run(run_id: str, **fields) -> dict | None:
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    if _check_supabase_tables():
        try:
            db = get_active_db()
            res = db.table("verification_runs").update(fields).eq("id", run_id).execute()
            if res.data:
                run_data = res.data[0]
                run_data["persistence_backend"] = "supabase"
                return run_data
        except Exception as exc:
            log.warning("Supabase update verification_runs failed: %s", exc)
            if get_settings().app_env == "production":
                raise AppError(f"Database update failed in production: {exc}", status=500, code="database_error")

    return _fallback_store.update_run(run_id, **fields)


def save_stage(run_id: str, stage_name: str, stage_order: int, payload: dict, status: str = "completed") -> dict:
    """Persist a single stage for a run. Enforces uniqueness and idempotency."""
    existing = get_stage(run_id, stage_name)
    if existing:
        return existing

    if _check_supabase_tables():
        try:
            db = get_active_db()
            row = {
                "run_id": run_id,
                "stage_name": stage_name,
                "stage_order": stage_order,
                "status": status,
                "payload": payload,
            }
            res = db.table("verification_stages").upsert(
                row,
                on_conflict="run_id,stage_name",
                ignore_duplicates=True,
            ).execute()
            if res.data:
                return res.data[0]
            stage = get_stage(run_id, stage_name)
            if stage:
                return stage
        except Exception as exc:
            log.warning("Supabase save verification_stages failed: %s", exc)
            if get_settings().app_env == "production":
                raise AppError(f"Database save_stage failed in production: {exc}", status=500, code="database_error")

    return _fallback_store.save_stage(run_id, stage_name, stage_order, payload, status)


def get_stage(run_id: str, stage_name: str) -> dict | None:
    if _check_supabase_tables():
        try:
            db = get_active_db()
            res = (
                db.table("verification_stages")
                .select("*")
                .eq("run_id", run_id)
                .eq("stage_name", stage_name)
                .limit(1)
                .execute()
            )
            if res.data:
                return res.data[0]
            return None
        except Exception as exc:
            log.warning("Supabase get verification_stages failed: %s", exc)
            if get_settings().app_env == "production":
                raise AppError(f"Database get_stage failed: {exc}", status=500, code="database_error")

    return _fallback_store.get_stage(run_id, stage_name)


def list_stages(run_id: str) -> list[dict]:
    """Return all persisted stages for a run, strictly ordered by stage_order ASC."""
    if _check_supabase_tables():
        try:
            db = get_active_db()
            res = (
                db.table("verification_stages")
                .select("*")
                .eq("run_id", run_id)
                .order("stage_order", desc=False)
                .execute()
            )
            if res.data is not None:
                return res.data
        except Exception as exc:
            log.warning("Supabase list verification_stages failed: %s", exc)
            if get_settings().app_env == "production":
                raise AppError(f"Database list_stages failed: {exc}", status=500, code="database_error")

    return _fallback_store.list_stages(run_id)


def get_completed_stage_names(run_id: str) -> list[str]:
    stages = list_stages(run_id)
    return [s["stage_name"] for s in stages if s.get("status") == "completed"]


def reset_dev_store() -> None:
    """Helper for testing to reset local development store."""
    global _fallback_store
    _fallback_store.reset()
