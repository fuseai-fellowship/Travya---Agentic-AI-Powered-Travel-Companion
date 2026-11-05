import pytest

from app.core.errors import InvalidInput, NotFound
from app.integrations.storage.database import DatabaseStorage

pytestmark = pytest.mark.db


async def test_database_storage_round_trip(clean_db: None) -> None:
    storage = DatabaseStorage()
    await storage.put("documents/u1/a", b"%PDF-1.7 one", "application/pdf")
    assert await storage.get("documents/u1/a") == b"%PDF-1.7 one"
    await storage.put("documents/u1/a", b"%PDF-1.7 two", "application/pdf")
    assert await storage.get("documents/u1/a") == b"%PDF-1.7 two"
    assert await storage.download_url("documents/u1/a", "a.pdf") is None
    await storage.delete("documents/u1/a")
    with pytest.raises(NotFound):
        await storage.get("documents/u1/a")
    with pytest.raises(InvalidInput):
        await storage.put("../escape", b"x", "text/plain")
