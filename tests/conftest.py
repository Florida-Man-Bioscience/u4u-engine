"""
Shared test fixtures for the u4u-engine test suite.
"""

import os
import tempfile
import pytest

# The API authenticates by default (fails closed). Tests exercise endpoints
# directly via TestClient, so enable the explicit dev/test override before the
# app module is imported.
os.environ.setdefault("ALLOW_INSECURE_NO_AUTH", "1")

from engine.annotators import cache as cache_module


@pytest.fixture(autouse=True)
def isolated_annotation_cache(tmp_path):
    """Give each test its own empty in-memory annotation cache."""
    db_path = str(tmp_path / "test_annotation_cache.db")
    old_cache = cache_module.annotation_cache
    cache_module.annotation_cache = cache_module.AnnotationCache(db_path)

    # Patch all annotators that imported the singleton
    import engine.annotators.vep as vep
    import engine.annotators.clinvar as clinvar
    import engine.annotators.gnomad as gnomad
    import engine.annotators.myvariant as myvariant
    import engine.annotators.uniprot as uniprot
    import engine.annotators.pharmgkb as pharmgkb
    import engine.annotators.gwas_catalog as gwas_catalog

    modules = [vep, clinvar, gnomad, myvariant, uniprot, pharmgkb, gwas_catalog]
    for mod in modules:
        mod.annotation_cache = cache_module.annotation_cache

    yield

    cache_module.annotation_cache = old_cache
    for mod in modules:
        mod.annotation_cache = old_cache
