"""Per-test isolation for the regulatory cache and the LRU-cached YAML loaders."""

import pytest

from engine.regulatory import cache as cache_module
from engine.regulatory import store as store_module
from engine.regulatory.sources import (
    _base,
    clinicaltrials,
    federal_register,
    openfda,
    regulations_gov,
)


@pytest.fixture(autouse=True)
def isolated_regulatory_cache(tmp_path):
    """Give each regulatory test its own SQLite cache file."""
    db_path = str(tmp_path / "test_regulatory_cache.db")
    new_cache = cache_module.RegulatoryCache(db_path)

    old_module_cache = cache_module.regulatory_cache
    cache_module.regulatory_cache = new_cache

    # The _base module imports `regulatory_cache` by name — repoint it.
    old_base_cache = _base.regulatory_cache
    _base.regulatory_cache = new_cache

    yield

    cache_module.regulatory_cache = old_module_cache
    _base.regulatory_cache = old_base_cache


@pytest.fixture(autouse=True)
def reset_store_cache():
    """Drop the lru_cache on YAML loaders so per-test data overrides apply."""
    store_module.reset_cache()
    yield
    store_module.reset_cache()
