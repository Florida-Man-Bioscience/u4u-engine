"""
Wave 3b — pipeline-enrichment wiring.

Proves the persistence/threading that lets the PRS-inflammatory and BPC-157
responder feature adapters fire in production: enrichment is stored per patient
(``patient_enrichment``) and ``analysis.predict_response`` threads it into the
``ResponderContext.extra`` channels the adapters read. Without enrichment the
adapters stay a graceful no-op (the pre-Wave-3b behaviour).
"""
import json
import random

from engine.tracking import analysis, service
from engine.tracking.genetics import generate_synthetic_profile

# A prs_profile shaped exactly as the pipeline emits it, with an informative
# systemic-inflammation score (≥ _MIN_INFLAM_VARIANTS genotyped, high percentile).
_PRS_PROFILE = {
    "trait_scores": {
        "systemic_inflammation": {"variants_found": 5, "prs_score": 0.9},
    },
}
# A BPC-157 composite prediction with at least one contributing locus (so the
# adapter fires — a composite of ~0 from absence of loci must NOT fire).
_BPC157 = {
    "composite_score": 3.4,
    "pathways_affected": [{"pathway": "VEGF/angiogenesis"}],
    "candidate_factors": [],
}


def _feature_names(result: dict) -> set[str]:
    return {f["name"] for f in result["responder_features"]}


def test_patient_enrichment_round_trip(conn):
    p = service.create_patient(conn, label="ENR-1")
    assert service.get_patient_enrichment(conn, p.id) is None  # absent → None
    service.set_patient_enrichment(conn, p.id, json.dumps(_PRS_PROFILE))
    got = service.get_patient_enrichment(conn, p.id)
    assert got == _PRS_PROFILE
    # Upsert replaces.
    service.set_patient_enrichment(conn, p.id, json.dumps({"prs_profile": {}}))
    assert service.get_patient_enrichment(conn, p.id) == {"prs_profile": {}}


def test_patient_enrichment_malformed_json_is_none(conn):
    p = service.create_patient(conn, label="ENR-2")
    # Write a non-JSON / non-object blob directly, bypassing the JSON encoder.
    service.set_patient_enrichment(conn, p.id, "not valid json")
    assert service.get_patient_enrichment(conn, p.id) is None
    service.set_patient_enrichment(conn, p.id, json.dumps([1, 2, 3]))  # not an object
    assert service.get_patient_enrichment(conn, p.id) is None


def test_predict_response_fires_adapters_with_enrichment(conn):
    """With enrichment persisted, predict_response threads it into the responder
    context and BOTH the PRS-inflammatory and BPC-157 adapters fire (BPC-157 is
    in the PRS mask and is the BPC-157 adapter's peptide)."""
    p = service.create_patient(conn, label="ENR-3")
    service.set_genetic_profile(
        conn, p.id, generate_synthetic_profile(random.Random(0)).to_json()
    )
    service.set_patient_enrichment(
        conn, p.id, json.dumps({"prs_profile": _PRS_PROFILE, "bpc157": _BPC157})
    )

    result = analysis.predict_response(
        conn, patient_id=p.id, peptide_name="BPC-157", biomarker_name="Serum VEGF",
    )
    names = _feature_names(result)
    assert "genetics" in names                      # anchored feature always present
    assert "prs_inflammatory_baseline" in names     # PRS enrichment fired
    assert "bpc157_composite" in names               # BPC-157 enrichment fired


def test_predict_response_no_enrichment_is_graceful_noop(conn):
    """Same patient/peptide WITHOUT enrichment: only the genetics feature is
    present — the enrichment adapters no-op, exactly the pre-Wave-3b behaviour."""
    p = service.create_patient(conn, label="ENR-4")
    service.set_genetic_profile(
        conn, p.id, generate_synthetic_profile(random.Random(0)).to_json()
    )
    result = analysis.predict_response(
        conn, patient_id=p.id, peptide_name="BPC-157", biomarker_name="Serum VEGF",
    )
    names = _feature_names(result)
    assert "genetics" in names
    assert "prs_inflammatory_baseline" not in names
    assert "bpc157_composite" not in names
