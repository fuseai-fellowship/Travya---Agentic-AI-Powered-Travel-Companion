"""FastAPI dependencies: database session, authenticated user, integrations, rate limits."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.adk.sessions import BaseSessionService
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.errors import Forbidden, Unauthorized
from app.core.ratelimit import Limiter
from app.core.security import Principal, verify_id_token
from app.integrations.registry import Integrations
from app.models import User
from app.services.users import get_or_create_user

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_bearer = HTTPBearer(auto_error=False, description="Firebase ID token")


async def get_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if credentials is None or not credentials.credentials:
        raise Unauthorized()
    return await verify_id_token(credentials.credentials)


PrincipalDep = Annotated[Principal, Depends(get_principal)]


def get_limiter(request: Request) -> Limiter:
    return request.app.state.limiter  # type: ignore[no-any-return]


LimiterDep = Annotated[Limiter, Depends(get_limiter)]


async def get_current_user(
    principal: PrincipalDep, session: SessionDep, limiter: LimiterDep
) -> User:
    await limiter.hit(settings.RATE_LIMIT_DEFAULT, "api", principal.uid)
    return await get_or_create_user(session, principal)


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(principal: PrincipalDep) -> Principal:
    if not principal.is_admin:
        raise Forbidden("Administrator access required")
    return principal


AdminDep = Annotated[Principal, Depends(require_admin)]


def get_integrations(request: Request) -> Integrations:
    return request.app.state.integrations  # type: ignore[no-any-return]


IntegrationsDep = Annotated[Integrations, Depends(get_integrations)]


def get_adk_sessions(request: Request) -> BaseSessionService:
    return request.app.state.adk_sessions  # type: ignore[no-any-return]


AdkSessionsDep = Annotated[BaseSessionService, Depends(get_adk_sessions)]


def rate_limit(limit: str, scope: str) -> Callable[..., Awaitable[None]]:
    async def dependency(user: CurrentUser, limiter: LimiterDep) -> None:
        await limiter.hit(limit, scope, str(user.id))

    return dependency
