"""Core cross-cutting concerns: security, tenant context, error handling, pagination."""

from app.core.errors import (
    AppError,
    ContentNotFoundError,
    PersonaNotFoundError,
    PipelineError,
    PlatformAuthError,
    PublishError,
    RateLimitError,
    StageAbort,
    StageSkip,
    TenantNotFoundError,
    register_error_handlers,
)
from app.core.pagination import paginate, paginated_response, pagination_params
from app.core.security import (
    Role,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    role_ge,
    verify_password,
)
from app.core.tenant import (
    get_current_tenant_id,
    inject_tenant_filter,
    set_current_tenant_id,
)

__all__ = [
    "AppError",
    "ContentNotFoundError",
    "PersonaNotFoundError",
    "PipelineError",
    "PlatformAuthError",
    "PublishError",
    "RateLimitError",
    "StageAbort",
    "StageSkip",
    "TenantNotFoundError",
    "register_error_handlers",
    "paginate",
    "paginated_response",
    "pagination_params",
    "Role",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_password",
    "role_ge",
    "verify_password",
    "get_current_tenant_id",
    "inject_tenant_filter",
    "set_current_tenant_id",
]