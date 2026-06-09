import pytest

from engine.tracking import db, get_conn


@pytest.fixture
def conn():
    db.reset_initialized()
    c = get_conn(":memory:")
    yield c
    c.close()
