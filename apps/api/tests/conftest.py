import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.services import auth_service

engine = create_engine(settings.DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestSessionLocal()
    try:
        yield session
    finally:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    unique = uuid.uuid4().hex[:8]
    return auth_service.register_user(
        db_session,
        UserCreate(email=f"user_{unique}@test.com", password="TestPass123!", full_name="Test User"),
    )


@pytest.fixture
def auth_headers(test_user: User, db_session: Session) -> dict[str, str]:
    access_token, _ = auth_service.issue_tokens(db_session, test_user)
    return {"Authorization": f"Bearer {access_token}"}
