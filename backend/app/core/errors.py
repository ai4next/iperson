"""Domain-specific exceptions & FastAPI exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status


class AppError(Exception):
    """Base domain error — all custom errors inherit from this."""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class TenantNotFoundError(AppError):
    ...


class PersonaNotFoundError(AppError):
    ...


class ContentNotFoundError(AppError):
    ...


class PipelineError(AppError):
    ...


class StageSkip(AppError):
    """Raise inside a pipeline stage to skip it gracefully."""

    def __init__(self, stage: str, reason: str = "") -> None:
        super().__init__(f"Stage '{stage}' skipped: {reason}", code="STAGE_SKIP")
        self.stage = stage


class StageAbort(AppError):
    """Raise inside a pipeline stage to abort the entire pipeline."""

    def __init__(self, stage: str, reason: str = "") -> None:
        super().__init__(f"Pipeline aborted at '{stage}': {reason}", code="STAGE_ABORT")
        self.stage = stage


class PlatformAuthError(AppError):
    ...


class PublishError(AppError):
    ...


class RateLimitError(AppError):
    ...


# ── FastAPI integration ────────────────────────────────────────────────

_error_map: dict[type[AppError], int] = {
    TenantNotFoundError: status.HTTP_404_NOT_FOUND,
    PersonaNotFoundError: status.HTTP_404_NOT_FOUND,
    ContentNotFoundError: status.HTTP_404_NOT_FOUND,
    PipelineError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    PlatformAuthError: status.HTTP_401_UNAUTHORIZED,
    PublishError: status.HTTP_502_BAD_GATEWAY,
    RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
}


def register_error_handlers(app: FastAPI) -> None:
    """Attach domain-error handlers to a FastAPI instance."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_, exc: AppError):
        http_code = _error_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=http_code, detail={"message": exc.message, "code": exc.code})