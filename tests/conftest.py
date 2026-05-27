"""
Shared test fixtures for the u4u-engine test suite.
"""

import pytest
from engine.annotators.cache import annotation_cache


@pytest.fixture(autouse=True)
def clear_annotation_cache():
    """Clear the annotation cache before each test to prevent cross-test leakage."""
    conn = annotation_cache._conn()
    conn.execute("DELETE FROM annotation_cache")
    conn.commit()
