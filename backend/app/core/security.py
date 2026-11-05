"""Firebase Authentication: the backend only verifies ID tokens.

Sign-up, sign-in, password reset, email verification and anonymous "try demo" sessions are handled
by Firebase. Locally the Auth emulator is used (FIREBASE_AUTH_EMULATOR_HOST), so no real project is needed.
"""

from dataclasses import dataclass
from typing import Any

import anyio
import firebase_admin
from firebase_admin import auth

from app.core.config import settings
from app.core.errors import Unauthorized
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Principal:
    uid: str
    email: str | None
    name: str | None
    is_anonymous: bool
    is_admin: bool


def init_firebase() -> None:
    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})


def _principal_from_claims(claims: dict[str, Any]) -> Principal:
    provider = claims.get("firebase", {}).get("sign_in_provider")
    return Principal(
        uid=claims["uid"],
        email=claims.get("email"),
        name=claims.get("name"),
        is_anonymous=provider == "anonymous",
        is_admin=bool(claims.get("admin")),
    )


async def verify_id_token(token: str) -> Principal:
    try:
        claims = await anyio.to_thread.run_sync(
            lambda: auth.verify_id_token(token, clock_skew_seconds=10)
        )
    except (auth.ExpiredIdTokenError, auth.RevokedIdTokenError) as exc:
        raise Unauthorized("Session expired, please sign in again") from exc
    except (auth.InvalidIdTokenError, ValueError) as exc:
        raise Unauthorized("Invalid credentials") from exc
    return _principal_from_claims(claims)


async def delete_firebase_user(uid: str) -> None:
    try:
        await anyio.to_thread.run_sync(lambda: auth.delete_user(uid))
    except auth.UserNotFoundError:
        log.info("firebase_user_already_deleted", uid=uid)
