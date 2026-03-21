import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone


class MockVerification:
    """A mock verification object that properly serializes to JSON"""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid4())
        self.entity_type = kwargs.get("entity_type", "herb")
        self.entity_id = kwargs.get("entity_id", "herb-123")
        self.field_name = kwargs.get("field_name")
        self.claimed_value = kwargs.get("claimed_value", "测试内容")
        self.source_id = kwargs.get("source_id")
        self.status = kwargs.get("status", "pending")
        self.applicant_id = kwargs.get("applicant_id", uuid4())
        self.verifier_id = kwargs.get("verifier_id")
        self.verdict = kwargs.get("verdict")
        self.verified_at = kwargs.get("verified_at")
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.evidence_list = kwargs.get("evidence_list", [])

    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        return {
            "id": str(self.id),
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "field_name": self.field_name,
            "claimed_value": self.claimed_value,
            "source_id": str(self.source_id) if self.source_id else None,
            "status": self.status,
            "applicant_id": str(self.applicant_id),
            "verifier_id": str(self.verifier_id) if self.verifier_id else None,
            "verdict": self.verdict,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "evidence_list": self.evidence_list
        }


# Mock database session fixture
@pytest.fixture
async def mock_db():
    """Create a mock database session"""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
async def client(mock_db):
    """Create a test client with mocked database dependency"""
    from app.main import app
    from app.core.database import get_db

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_neo4j_driver():
    """Create a mock Neo4j async driver with session context manager.

    Usage in tests:
        svc.driver = mock_neo4j_driver
        # Then configure mock_neo4j_driver.session().__aenter__().run.return_value
    """
    session = AsyncMock()
    session.run = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)

    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    driver.close = AsyncMock()
    return driver


@pytest.fixture
def mock_verification_model():
    """Create a mock VerificationModel instance"""
    return MockVerification()


@pytest.fixture
def verification_data():
    """Sample verification creation data"""
    return {
        "entity_type": "herb",
        "entity_id": "herb-123",
        "claimed_value": "人参能大补元气",
        "applicant_id": str(uuid4()),
        "field_name": "efficacy"
    }
