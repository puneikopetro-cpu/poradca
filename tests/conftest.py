"""
Shared fixtures for all tests.

Uses an in-memory SQLite database, isolated per test session.
The app's get_db dependency is overridden to use this test DB.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client):
    """Register a user and return their credentials."""
    payload = {
        "email": "user@test.sk",
        "password": "testpass123",
        "full_name": "Test User",
        "phone": "+421900000000",
    }
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201
    return payload


@pytest.fixture()
def auth_headers(client, registered_user):
    """Return Authorization headers for a logged-in user."""
    r = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def profile_payload():
    return {
        "monthly_income": 3000.0,
        "monthly_expenses": 1500.0,
        "total_savings": 15000.0,
        "total_debt": 0.0,
        "age": 30,
        "investment_experience": 3,
        "investment_horizon": "long",
        "goal_type": "retirement",
    }
