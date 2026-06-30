"""
Shared test fixtures for the u4u-engine test suite.
"""

import tempfile

import pytest

from engine.annotators import cache as cache_module


@pytest.fixture(autouse=True)
def isolated_annotation_cache(tmp_path):
    """Give each test its own empty in-memory annotation cache."""
    db_path = str(tmp_path / "test_annotation_cache.db")
    old_cache = cache_module.annotation_cache
    cache_module.annotation_cache = cache_module.AnnotationCache(db_path)

    # Patch all annotators that imported the singleton
    import engine.annotators.clinvar as clinvar
    import engine.annotators.gnomad as gnomad
    import engine.annotators.gwas_catalog as gwas_catalog
    import engine.annotators.myvariant as myvariant
    import engine.annotators.pharmgkb as pharmgkb
    import engine.annotators.uniprot as uniprot
    import engine.annotators.vep as vep

    modules = [vep, clinvar, gnomad, myvariant, uniprot, pharmgkb, gwas_catalog]
    for mod in modules:
        mod.annotation_cache = cache_module.annotation_cache

    yield

    cache_module.annotation_cache = old_cache
    for mod in modules:
        mod.annotation_cache = old_cache
