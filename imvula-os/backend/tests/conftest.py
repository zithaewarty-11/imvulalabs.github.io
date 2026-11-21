import os

os.environ["DATABASE_URL"] = "sqlite:///./test_imvula.db"

import pytest

from app.core.database import Base, engine


@pytest.fixture(autouse=True)
def fresh_db():
    """Before each test: wipe the DB and rebuild it clean."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
