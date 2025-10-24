"""
Test configuration and fixtures for comprehensive testing.
"""
import os
import pytest
from unittest.mock import Mock, patch
from sqlmodel import Session, create_engine, SQLModel
from redis import Redis
from fastapi.testclient import TestClient

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"  # Use different DB for tests
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_DB"] = "test_travya"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "changethis"

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app

# Create test database engine
test_engine = create_engine(
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
    echo=False,
)

@pytest.fixture(scope="session")
def test_db():
    """Create test database tables."""
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture
def db_session(test_db):
    """Create database session for tests."""
    with Session(test_db) as session:
        yield session

@pytest.fixture
def mock_redis():
    """Mock Redis connection for tests."""
    mock_redis = Mock(spec=Redis)
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.set.return_value = True
    return mock_redis

@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_llm():
    """Mock LLM responses."""
    mock_llm = Mock()
    mock_llm.generate.return_value = "Mock AI response"
    return mock_llm

@pytest.fixture
def mock_agent():
    """Mock agent for testing."""
    mock_agent = Mock()
    mock_agent.name = "test_agent"
    mock_agent.description = "Test agent"
    mock_agent.run.return_value = {"answer": "Mock response", "context": []}
    return mock_agent
