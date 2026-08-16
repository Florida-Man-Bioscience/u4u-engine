"""Tests for the leave-one-out predictive-performance backtest
(``engine.tracking.diagnostics``)."""
from engine.tracking import diagnostics, service


def _seed_series(conn, *, label, start, values, peptide="CJC-1295",
                 biomarker="Serum IGF-1"):
    """One patient, one treatment, a rising IGF-1 series."""
    p = service.create_patient(conn, label=label)
    service.create_treatment(
        conn, patient_id=p.id, peptide_name=peptide,
        dose=2.0, dose_unit="mg", start_date=start,
    )
    for date, val in values:
        service.create_measurement(
            conn, patient_id=p.id, biomarker_name=biomarker,
            value=val, measured_at=date, modality="hormone", unit="ng/mL",
        )
    return p


def _rising(conn, label, start):
    return _seed_series(
        conn, label=label, start=start,
        values=[
            (start, 180.0),
            (_plus_weeks(start, 4), 225.0),
            (_plus_weeks(start, 8), 255.0),
            (_plus_weeks(start, 12), 270.0),
        ],
    )


def _plus_weeks(iso: str, weeks: int) -> str:
    from datetime import date, timedelta

    y, m, d = (int(x) for x in iso.split("-"))
    return (date(y, m, d) + timedelta(weeks=weeks)).isoformat()


def test_diagnostics_empty_when_no_data(conn):
    out = diagnostics.run_diagnostics(conn, [])
    assert out["n_points"] == 0
    assert out["n_series"] == 0
    assert out["overall"]["coverage_95"] is None
    assert out["points"] == []


def test_diagnostics_backtests_a_series(conn):
    p = _rising(conn, "A", "2026-01-01")
    out = diagnostics.run_diagnostics(conn, [p])

    assert out["n_series"] == 1
    # 4 points, one is the pre-baseline anchor (w<1) which is never held out,
    # and each held-out fit needs >=2 training points → 3 held-out predictions.
    assert out["n_points"] == 3
    assert out["overall"]["coverage_95"] is not None
    assert 0.0 <= out["overall"]["coverage_95"] <= 1.0
    assert out["overall"]["mae_pct"] is not None
    assert out["overall"]["rmse_pct"] >= out["overall"]["mae_pct"]

    # Every point carries a predicted band bracketing predicted mean.
    for pt in out["points"]:
        assert pt["predicted_lo_95"] <= pt["predicted"] <= pt["predicted_hi_95"]
        assert pt["peptide"] == "CJC-1295"
        assert pt["biomarker"] == "Serum IGF-1"


def test_diagnostics_breakdowns_and_scoping(conn):
    a = _rising(conn, "A", "2026-01-01")
    b = _rising(conn, "B", "2026-02-01")

    both = diagnostics.run_diagnostics(conn, [a, b])
    assert both["n_series"] == 2
    assert both["n_patients"] == 2
    # One peptide, one biomarker across the cohort.
    assert [g["label"] for g in both["by_peptide"]] == ["CJC-1295"]
    assert [g["label"] for g in both["by_biomarker"]] == ["Serum IGF-1"]
    assert both["by_peptide"][0]["n_series"] == 2

    # Scoping to a single patient halves the series count.
    one = diagnostics.run_diagnostics(conn, [a])
    assert one["n_series"] == 1


def test_diagnostics_skips_short_series(conn):
    # Only two measurements → below MIN_SERIES_POINTS, nothing to backtest.
    p = _seed_series(
        conn, label="Short", start="2026-01-01",
        values=[("2026-01-01", 180.0), ("2026-02-01", 220.0)],
    )
    out = diagnostics.run_diagnostics(conn, [p])
    assert out["n_series"] == 0
    assert out["n_points"] == 0


def test_diagnostics_does_not_mix_treatments(conn):
    """A second peptide's series must not pollute the first peptide's backtest."""
    p = service.create_patient(conn, label="Mix")
    t1 = service.create_treatment(
        conn, patient_id=p.id, peptide_name="CJC-1295",
        dose=2.0, dose_unit="mg", start_date="2026-01-01",
    )
    t2 = service.create_treatment(
        conn, patient_id=p.id, peptide_name="Semaglutide",
        dose=1.0, dose_unit="mg", start_date="2026-02-01",
    )
    for date, val in [
        ("2026-01-01", 180.0), ("2026-01-29", 225.0),
        ("2026-02-26", 255.0), ("2026-03-26", 270.0),
    ]:
        service.create_measurement(
            conn, patient_id=p.id, treatment_id=t1.id,
            biomarker_name="Serum IGF-1", value=val,
            measured_at=date, modality="hormone", unit="ng/mL",
        )
    for date, val in [
        ("2026-02-01", 95.0), ("2026-03-01", 90.0),
        ("2026-04-01", 86.0), ("2026-05-01", 83.0),
    ]:
        service.create_measurement(
            conn, patient_id=p.id, treatment_id=t2.id,
            biomarker_name="Body weight (GLP-1 RA)", value=val,
            measured_at=date, modality="physical", unit="kg",
        )
    out = diagnostics.run_diagnostics(conn, [p])
    peptides = {g["label"] for g in out["by_peptide"]}
    biomarkers = {g["label"] for g in out["by_biomarker"]}
    assert peptides == {"CJC-1295", "Semaglutide"}
    assert biomarkers == {"Serum IGF-1", "Body weight (GLP-1 RA)"}
    assert all(pt["peptide"] != "CJC-1295" or pt["biomarker"] == "Serum IGF-1"
               for pt in out["points"])
    assert all(pt["peptide"] != "Semaglutide" or pt["biomarker"] == "Body weight (GLP-1 RA)"
               for pt in out["points"])
