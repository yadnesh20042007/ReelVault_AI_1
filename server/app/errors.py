from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    status, code = 400, "bad_request"

    def __init__(self, message: str = "", *, status: int | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        if status:
            self.status = status
        if code:
            self.code = code


class InvalidURL(AppError):
    status, code = 422, "invalid_url"


class Unauthorized(AppError):
    status, code = 401, "unauthorized"


class NotFound(AppError):
    status, code = 404, "not_found"


class RateLimited(AppError):
    status, code = 429, "rate_limited"


class NoContent(AppError):
    status, code = 422, "no_content"


class UpstreamFailed(AppError):
    status, code = 502, "upstream_failed"


class AuthError(AppError):
    status, code = 400, "auth_error"


class PipelineError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handler(_: Request, e: AppError):
        return JSONResponse(status_code=e.status, content={"error": {"code": e.code, "message": e.message}})

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, e: StarletteHTTPException):
        message = e.detail if isinstance(e.detail, str) else "The request could not be completed."
        return JSONResponse(status_code=e.status_code, content={"error": {"code": "http_error", "message": message}})

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        first = e.errors()[0] if e.errors() else {}
        message = first.get("msg") or "Invalid request."
        return JSONResponse(status_code=422, content={"error": {"code": "invalid_request", "message": message}})

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, e: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": str(e) or "The request could not be completed."}},
        )
