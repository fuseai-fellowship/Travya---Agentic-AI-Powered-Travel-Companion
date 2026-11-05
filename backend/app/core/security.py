"""Firebase Authentication: the backend only verifies ID tokens.

Sign-up, sign-in, password reset, email verification and anonymous "try demo" sessions are handled
by Firebase. Locally the Auth emulator is used (FIREBASE_AUTH_EMULATOR_HOST), so no real project is needed.
"""

from dataclasses import dataclass
from typing import Any

import anyio
import firebase_admin
import google.auth
import google.auth.credentials
import google.auth.exceptions
from firebase_admin import auth, credentials

from app.core.config import settings
from app.core.errors import Unauthorized, UpstreamUnavailable
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Principal:
    uid: str
    email: str | None
    name: str | None
    is_anonymous: bool
    is_admin: bool


class _PublicCredential(credentials.Base):  # type: ignore[misc]
    """For hosts without Google credentials (e.g. Hugging Face Spaces).

    Verifying ID tokens only needs Google's public signing certificates; admin calls such as
    deleting a user fail softly instead (the client deletes its own Firebase user).
    """

    def get_credential(self) -> google.auth.credentials.Credentials:
        return google.auth.credentials.AnonymousCredentials()  # type: ignore[no-untyped-call]


def _credential() -> credentials.Base:
    try:
        google.auth.default()
    except google.auth.exceptions.DefaultCredentialsError:
        log.info("firebase_public_credential", reason="no application default credentials")
        return _PublicCredential()
    return credentials.ApplicationDefault()


def init_firebase() -> None:
    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            credential=_credential(), options={"projectId": settings.FIREBASE_PROJECT_ID}
        )


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
    except auth.CertificateFetchError as exc:
        # Google's signing certificates are out of reach: our problem, not the user's token.
        log.warning("firebase_certificates_unavailable", error=str(exc)[:200])
        raise UpstreamUnavailable(
            "Sign-in can't be checked right now. Please retry shortly."
        ) from exc
    except (auth.ExpiredIdTokenError, auth.RevokedIdTokenError) as exc:
        raise Unauthorized("Session expired, please sign in again") from exc
    except (auth.InvalidIdTokenError, ValueError) as exc:
        raise Unauthorized("Invalid credentials") from exc
    return _principal_from_claims(claims)


async def delete_firebase_user(uid: str) -> None:
    """Best effort: hosts without Google credentials leave this to the client (Firebase deleteUser)."""
    try:
        await anyio.to_thread.run_sync(lambda: auth.delete_user(uid))
    except auth.UserNotFoundError:
        log.info("firebase_user_already_deleted", uid=uid)
    except Exception as exc:
        log.warning("firebase_user_not_deleted", uid=uid, error=type(exc).__name__)
