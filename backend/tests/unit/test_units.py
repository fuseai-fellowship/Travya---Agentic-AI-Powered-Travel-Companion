import pytest

from app.agents.events import AgentEvent
from app.core.config import Settings
from app.core.errors import BudgetExhausted, RateLimited
from app.core.ratelimit import Limiter
from app.core.security import _principal_from_claims
from app.services.documents import safe_filename, sniff_content_type
from app.services.knowledge import _chunks, destination_key


def test_production_settings_require_secrets() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        Settings(ENVIRONMENT="production", _env_file=None)  # type: ignore[call-arg]


def test_principal_from_firebase_claims() -> None:
    anonymous = _principal_from_claims({"uid": "u1", "firebase": {"sign_in_provider": "anonymous"}})
    assert anonymous.is_anonymous and not anonymous.is_admin
    admin = _principal_from_claims(
        {"uid": "u2", "email": "a@b.c", "admin": True, "firebase": {"sign_in_provider": "password"}}
    )
    assert admin.is_admin and admin.email == "a@b.c" and not admin.is_anonymous


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"%PDF-1.7 ...", "application/pdf"),
        (b"\x89PNG\r\n\x1a\n....", "image/png"),
        (b"\xff\xd8\xff\xe0....", "image/jpeg"),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 ", "image/webp"),
        (b"RIFF\x00\x00\x00\x00AVI ", None),
        (b"MZ\x90\x00", None),
        (b"<script>alert(1)</script>", None),
    ],
)
def test_upload_type_is_sniffed_from_bytes(data: bytes, expected: str | None) -> None:
    assert sniff_content_type(data) == expected


def test_safe_filename_strips_paths_and_controls() -> None:
    assert safe_filename("../../etc/passwd") == "etcpasswd"
    assert safe_filename('ticket"; rm -rf.pdf') == "ticket rm -rf.pdf"
    assert safe_filename("...") == "document"


async def test_rate_limit_and_budget() -> None:
    limiter = Limiter("async+memory://")
    await limiter.hit("2/minute", "scope", "user")
    await limiter.hit("2/minute", "scope", "user")
    with pytest.raises(RateLimited) as info:
        await limiter.hit("2/minute", "scope", "user")
    assert info.value.retry_after and info.value.retry_after > 0
    await limiter.hit("2/minute", "scope", "other-user")


async def test_llm_budget_is_global(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import ratelimit

    monkeypatch.setattr(ratelimit.settings, "LLM_DAILY_REQUEST_BUDGET", 1)
    limiter = Limiter("async+memory://")
    await limiter.check_llm_budget()
    await limiter.spend_llm_budget()
    assert await limiter.remaining_llm_budget() == 0
    with pytest.raises(BudgetExhausted):
        await limiter.check_llm_budget()
    with pytest.raises(BudgetExhausted):
        await limiter.spend_llm_budget()


def test_guide_chunking_and_keys() -> None:
    text = "\n".join(f"Paragraph {i} " + "x" * 300 for i in range(6))
    chunks = _chunks("See", text)
    assert len(chunks) >= 2 and all(c.startswith("See: ") for c in chunks)
    assert destination_key("  Kathmandu,  Nepal ") == "kathmandu"


def test_agent_event_sse_shape() -> None:
    event = AgentEvent(agent="planner", kind="result", message="Drafted 3 days")
    payload = event.sse()
    assert payload["event"] == "result"
    assert '"agent":"planner"' in payload["data"]


def test_firebase_credential_without_google_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    import google.auth
    import google.auth.credentials
    import google.auth.exceptions

    from app.core import security

    def no_adc(*_: object, **__: object) -> None:
        raise google.auth.exceptions.DefaultCredentialsError("none")

    monkeypatch.setattr(google.auth, "default", no_adc)
    credential = security._credential()
    assert isinstance(credential, security._PublicCredential)
    assert isinstance(credential.get_credential(), google.auth.credentials.AnonymousCredentials)


async def test_limiter_falls_back_to_memory_when_redis_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core import ratelimit

    monkeypatch.setattr(ratelimit.settings, "LLM_DAILY_REQUEST_BUDGET", 5)
    limiter = Limiter("async+redis://localhost:1")  # nothing listens there
    await limiter.hit("1/minute", "scope", "user")
    with pytest.raises(RateLimited):
        await limiter.hit("1/minute", "scope", "user")
    await limiter.spend_llm_budget()
    assert await limiter.remaining_llm_budget() == 4


async def test_limiter_falls_back_when_redis_stalls(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    from app.core import ratelimit

    async def stall(*_: object) -> bool:
        await asyncio.sleep(5)
        return True

    monkeypatch.setattr(ratelimit, "STORAGE_TIMEOUT_S", 0.05)
    limiter = Limiter("async+memory://")
    monkeypatch.setattr(limiter._shared.moving, "hit", stall)
    await limiter.hit("1/minute", "scope", "user")
    with pytest.raises(RateLimited):
        await limiter.hit("1/minute", "scope", "user")


async def test_unhandled_errors_keep_cors_headers() -> None:
    from httpx import ASGITransport, AsyncClient

    from app.core.config import settings
    from app.main import create_app

    application = create_app()

    async def boom() -> None:
        raise RuntimeError("unexpected")

    application.add_api_route("/boom", boom)
    origin = settings.FRONTEND_ORIGINS[0]
    transport = ASGITransport(app=application, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        response = await http.get("/boom", headers={"Origin": origin})
        foreign = await http.get("/boom", headers={"Origin": "https://evil.example"})
    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == origin
    assert response.json()["title"] == "Internal server error"
    assert "access-control-allow-origin" not in foreign.headers


async def test_certificate_fetch_failure_is_a_503(monkeypatch: pytest.MonkeyPatch) -> None:
    from firebase_admin import auth

    from app.core import security
    from app.core.errors import UpstreamUnavailable

    def unreachable(*_: object, **__: object) -> None:
        raise auth.CertificateFetchError("Failed to fetch public key certificates", cause=None)

    monkeypatch.setattr(auth, "verify_id_token", unreachable)
    with pytest.raises(UpstreamUnavailable):
        await security.verify_id_token("token")
