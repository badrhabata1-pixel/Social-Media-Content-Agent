import pytest

from analytics import PostsDatabase
from app import app, get_posts_db


@pytest.fixture(autouse=True)
def posts_db():
    """Every test gets a fresh in-memory analytics database: no test writes data/analytics.db."""
    db = PostsDatabase(":memory:")
    db.init_db()
    app.dependency_overrides[get_posts_db] = lambda: db
    yield db
    app.dependency_overrides.pop(get_posts_db, None)
    db.close()
