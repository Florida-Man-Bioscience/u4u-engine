import pytest

from engine.tracking import db, get_conn


@pytest.fixture
def conn():
    db.reset_initialized()
    with get_conn(":memory:") as c:
        yield c
