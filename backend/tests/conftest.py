"""Shared fixtures for the integration and security suites.

The existing unit tests call route functions directly with hand-built namespaces.
That is fast but cannot see anything the ASGI stack does: dependency wiring, status
codes, header handling, or the absence of middleware. These fixtures boot the real
app against an in-memory SQLite database so a test can exercise a request the way a
client would, without needing Postgres or Redis running.

External inference is stubbed by default. A test that lets it through would either
hit the public Hugging Face Space or wait out its timeout, which makes the suite
slow and non-deterministic in exactly the places we care least about.
"""

import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.core.security import hash_password
from app.domain.enums import UserRole
from app.inference.services import Result
from app.models.entities import User

# Importing entities is what populates Base.metadata; the import above is load-bearing
# even though the fixtures below only name User.
_ = Base


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture
async def engine():
    """One in-memory database per test, shared across connections via StaticPool.

    SQLite's default per-connection isolation would give the app and the test their
    own empty databases, so StaticPool is required rather than a tuning choice.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def sessionmaker(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db(sessionmaker) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        yield session


@pytest.fixture
def stub_classifier(monkeypatch) -> None:
    """Keep the external intent model out of the request path.

    Returns a fixed, confident prediction so routing decisions in a test are the
    test's own doing and not a side effect of whichever fallback branch ran.
    """
    from app.api.v1 import routes

    async def _classify(text: str, is_ocr: bool = False):
        return (
            Result("card_payment", 0.91, "test-stub-intent"),
            Result("medium", 0.80, "test-stub-priority"),
            Result("neutral", 0.80, "test-stub-sentiment"),
        )

    monkeypatch.setattr(routes, "classify", _classify)


@pytest_asyncio.fixture
async def app(sessionmaker, stub_classifier, tmp_path, monkeypatch):
    from app.api.v1 import routes
    from app.main import app as fastapi_app

    # Attachments must land in the test's own tmp_path; the configured default is a
    # real directory that would accumulate files across runs.
    monkeypatch.setattr(routes.settings, "storage_root", tmp_path)

    async def _get_db() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _get_db
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    # raise_app_exceptions=False lets the app's own 500 handler produce a response,
    # which is what a real client sees. Without it an unhandled error surfaces as a
    # test-side exception and the error path can never be asserted on.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as http:
        yield http


async def make_user(
    session: AsyncSession,
    *,
    role: UserRole,
    email: str | None = None,
    password: str = "CorrectHorse9!",
    is_active: bool = True,
) -> User:
    user = User(
        id=uuid.uuid4(),
        full_name=f"{role.value.title()} Tester",
        email=email or f"{role.value}-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    session.add(user)
    await session.commit()
    return user


@pytest_asyncio.fixture
async def customer(db) -> User:
    return await make_user(db, role=UserRole.customer)


@pytest_asyncio.fixture
async def other_customer(db) -> User:
    return await make_user(db, role=UserRole.customer)


@pytest_asyncio.fixture
async def agent(db) -> User:
    return await make_user(db, role=UserRole.agent)


@pytest_asyncio.fixture
async def administrator(db) -> User:
    return await make_user(db, role=UserRole.administrator)


def auth(user: User) -> dict[str, str]:
    from app.core.security import create_access_token

    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


async def open_ticket(client: AsyncClient, user: User, subject: str = "Card charged twice") -> str:
    response = await client.post(
        "/tickets",
        json={
            "subject": subject,
            "message": "My card was charged twice for one purchase this morning.",
        },
        headers=auth(user),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


# Exposed as fixtures as well as module functions so suites in tests/ subdirectories
# can use them without importing across package boundaries.
@pytest.fixture
def auth_headers():
    return auth


@pytest_asyncio.fixture
async def new_ticket(client):
    async def _open(user: User, subject: str = "Card charged twice") -> str:
        return await open_ticket(client, user, subject)

    return _open
