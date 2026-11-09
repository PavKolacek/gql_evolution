import uuid

from src.ServiceDefinitions.BaseService import ServiceExceptionWithCode
from . import errors


def get_user_id(ctx) -> uuid.UUID:
    """Vrátí id přihlášeného uživatele jako UUID (podporuje dict i objekt)."""
    user = ctx.user
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    if user_id is None:
        raise ServiceExceptionWithCode(
            "User is not authenticated", code=errors.NOT_AUTHENTICATED, location="get_user_id"
        )
    return uuid.UUID(user_id) if isinstance(user_id, str) else user_id