import logging
from fastapi import APIRouter, Depends, Body, Request
from pydantic import ValidationError

from app.config import get_settings
from app.db import verification_repo
from app.deps import AuthUser, current_user
from app.errors import AppError, NotFound, NoContent
from app.schemas.verification import (
    RVPackInput,
    StageRecordOut,
    VaultReminderConnectIn,
    VaultReminderConnectOut,
    VerificationRunOut,
)
from app.services.rvpack_parser import parse_rvpack
from app.services.verification_workflow import connect_deadline_to_vault, execute_run

log = logging.getLogger("api.verification")
router = APIRouter(prefix="/verification", tags=["verification"])


def _format_run_out(run: dict) -> VerificationRunOut:
    stages_data = verification_repo.list_stages(run["id"])
    completed_stage_names = [s["stage_name"] for s in stages_data if s.get("status") == "completed"]
    stages_out = [
        StageRecordOut(
            id=str(s["id"]),
            run_id=str(s["run_id"]),
            stage_name=s["stage_name"],
            stage_order=s["stage_order"],
            status=s.get("status", "completed"),
            payload=s.get("payload", {}),
            created_at=s.get("created_at", ""),
        )
        for s in stages_data
    ]

    # Find card payload if completed
    card_payload = None
    for s in stages_data:
        if s["stage_name"] == "card" and s.get("status") == "completed":
            card_payload = s.get("payload")
            break

    backend = run.get("persistence_backend") or verification_repo.get_storage_backend()

    return VerificationRunOut(
        id=str(run["id"]),
        user_id=str(run["user_id"]),
        user_reel_id=run.get("user_reel_id"),
        input_type=run.get("input_type", "rvpack"),
        status=run.get("status", "in_progress"),
        current_stage=run.get("current_stage", "extracted"),
        completed_stages=completed_stage_names,
        stages=stages_out,
        card=card_payload,
        persistence_backend=backend,
        created_at=run.get("created_at", ""),
        updated_at=run.get("updated_at", ""),
    )


@router.post(
    "/rvpack",
    response_model=VerificationRunOut,
    summary="Submit .rvpack Opportunity Package",
    description=(
        "Submit a .rvpack package containing TRANSCRIPT, ON_SCREEN, and META sections. "
        "Executes the five-stage verification pipeline in strict order: "
        "1. Extracted -> 2. Claims -> 3. Evidence -> 4. Verdict -> 5. Card."
    ),
)
def submit_rvpack(
    body: RVPackInput = Body(
        ...,
        description="The .rvpack package content containing TRANSCRIPT, ON_SCREEN, and META sections.",
        openapi_examples={
            "default": {
                "summary": "Hackathon India with ₹500 Fee and Deadline",
                "description": "Standard student opportunity package with fee scam warning and deadline.",
                "value": {
                    "content": (
                        "---TRANSCRIPT---\n"
                        "National AI Hackathon 2026 organized by IIT Bombay.\n"
                        "Registration fee is ₹500.\n"
                        "Application deadline is 15th December 2026.\n"
                        "Open to all engineering students.\n"
                        "Cash prize pool worth ₹5,00,000 and direct internship interviews.\n"
                        "---ON_SCREEN---\n"
                        "IIT Bombay AI Hackathon 2026\n"
                        "Apply online at https://iitb.ac.in/hackathon\n"
                        "Registration Fee: ₹500\n"
                        "---META---\n"
                        "author: IIT Bombay\n"
                        "title: IIT Bombay AI Hackathon 2026\n"
                        "category: hackathon\n"
                    ),
                    "reel_id": None,
                },
            }
        },
    ),
    user: AuthUser = Depends(current_user),
):
    """Submit a .rvpack text input with TRANSCRIPT, ON_SCREEN, and META sections.
    
    Creates a new verification run and executes the 5-stage verification workflow.
    """
    raw_content = body.content.strip()
    if not raw_content:
        raise AppError("No .rvpack content provided.", status=422, code="empty_rvpack_content")

    # Validate that the submitted content has recognizable structure or sections
    parsed = parse_rvpack(raw_content)
    if not parsed.sections_found or (not parsed.transcript and not parsed.on_screen and not parsed.meta):
        raise AppError(
            "Malformed .rvpack input: missing valid section headers. "
            "Input must contain at least one of: TRANSCRIPT, ON_SCREEN, or META.",
            status=422,
            code="malformed_rvpack",
        )

    # Fast check: ensure Gemini API keys are configured before launching verification pipeline
    keys = get_settings().get_all_gemini_keys()
    if not keys:
        raise AppError(
            "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment to perform verification.",
            status=503,
            code="llm_unconfigured",
        )

    run = verification_repo.create_run(
        user_id=user.id,
        raw_input=raw_content,
        input_type="rvpack",
        user_reel_id=body.reel_id,
    )

    try:
        execute_run(run["id"], user.id)
    except AppError as exc:
        log.warning("Verification pipeline returned AppError: %s", exc)
        verification_repo.update_run(run["id"], status="failed", error_message=str(exc))
        raise
    except Exception as exc:
        log.exception("Error executing verification run %s", run["id"])
        msg = str(exc).lower()
        if any(k in msg for k in ("504", "deadline_exceeded", "deadline exceeded", "timed out", "timeout")):
            timeout_msg = "Gemini model request timed out (504 DEADLINE_EXCEEDED). You can retry or resume this verification run."
            verification_repo.update_run(run["id"], status="failed", error_message=timeout_msg)
            raise AppError(timeout_msg, status=504, code="gemini_timeout") from exc
        verification_repo.update_run(run["id"], status="failed", error_message=str(exc))
        raise AppError(f"Verification pipeline failed: {exc}", status=500, code="pipeline_failed")

    latest_run = verification_repo.get_run(run["id"], user.id)
    return _format_run_out(latest_run or run)


@router.get("/runs/{run_id}", response_model=VerificationRunOut)
def get_run_status(
    run_id: str,
    user: AuthUser = Depends(current_user),
):
    """Fetch verification run details, show completed stages and card."""
    run = verification_repo.get_run(run_id, user.id)
    if not run:
        raise NotFound("Verification run not found.")
    return _format_run_out(run)


@router.post("/runs/{run_id}/resume", response_model=VerificationRunOut)
def resume_run(
    run_id: str,
    user: AuthUser = Depends(current_user),
):
    """Resume a verification run from the last completed stage without duplicating completed records."""
    keys = get_settings().get_all_gemini_keys()
    if not keys:
        raise AppError(
            "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment to perform verification.",
            status=503,
            code="llm_unconfigured",
        )

    run = verification_repo.get_run(run_id, user.id)
    if not run:
        raise NotFound("Verification run not found.")

    try:
        execute_run(run_id, user.id)
    except AppError as exc:
        log.warning("Resume pipeline returned AppError: %s", exc)
        verification_repo.update_run(run_id, status="failed", error_message=str(exc))
        raise
    except Exception as exc:
        log.exception("Error resuming verification run %s", run_id)
        msg = str(exc).lower()
        if any(k in msg for k in ("504", "deadline_exceeded", "deadline exceeded", "timed out", "timeout")):
            timeout_msg = "Gemini model request timed out (504 DEADLINE_EXCEEDED). You can retry or resume this verification run."
            verification_repo.update_run(run_id, status="failed", error_message=timeout_msg)
            raise AppError(timeout_msg, status=504, code="gemini_timeout") from exc
        verification_repo.update_run(run_id, status="failed", error_message=str(exc))
        raise AppError(f"Resume failed: {exc}", status=500, code="resume_failed")

    latest_run = verification_repo.get_run(run_id, user.id)
    return _format_run_out(latest_run or run)


@router.post("/runs/{run_id}/connect-vault-reminder", response_model=VaultReminderConnectOut)
def connect_vault_reminder(
    run_id: str,
    body: VaultReminderConnectIn = Body(default_factory=VaultReminderConnectIn),
    user: AuthUser = Depends(current_user),
):
    """Connect verified application deadline to Vault reminder feature.
    
    If the year is ambiguous, explicit confirmation of date is required.
    Prevents cross-user reminder creation and verifies reel ownership.
    """
    run = verification_repo.get_run(run_id, user.id)
    if not run:
        raise NotFound("Verification run not found.")

    try:
        res = connect_deadline_to_vault(
            run_id=run_id,
            user_id=user.id,
            reel_id=body.reel_id,
            label=body.label,
            explicit_date=body.event_date,
        )
        return VaultReminderConnectOut(**res)
    except PermissionError as perm_err:
        raise AppError(str(perm_err), status=403, code="forbidden")
    except ValueError as val_err:
        raise AppError(str(val_err), status=422, code="ambiguous_deadline_year")
    except Exception as exc:
        raise AppError(f"Could not connect Vault reminder: {exc}", status=500, code="vault_connect_failed")
