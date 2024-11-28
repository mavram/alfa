import os

import pytest

from alfa.config import settings
from alfa.db import Price, Stock, open_db


@pytest.fixture(scope="function")
def setup_database():
    db = open_db()
    db.connect()
    db.create_tables([Stock, Price])
    yield db  # Provides the initialized database to the test
    db.drop_tables([Stock, Price])
    db.close()
    # Remove test database
    os.remove(settings.DB_PATH)
