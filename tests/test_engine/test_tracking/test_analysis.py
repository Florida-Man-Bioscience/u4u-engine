from engine.tracking import analysis, service


def _seed_cohort(conn, *, peptide="CJC-1295", biomarker="Serum IGF-1"):
    """Two patients on the same dose, three timepoints each."""
    p1 = service.create_patient(conn, label="A")
    p2 = service.create_patient(conn, label="B")
    service.create_treatment(
        conn, patient_id=p1.id, peptide_name=peptide,
        dose=2.0, dose_unit="mg", start_date="2026-01-01",
    )
    service.create_treatment(
        conn, patient_id=p2.id, peptide_name=peptide,
        dose=2.0, dose_unit="mg", start_date="2026-02-01",
    )
    # baseline ~0w, mid ~4w, late ~8w (use real dates so weeks_between is meaningful)
    points = [
        (p1.id, "2026-01-02", 180.0),
        (p1.id, "2026-01-29", 230.0),  # ~4w
        (p1.id, "2026-02-26", 270.0),  # ~8w
        (p2.id, "2026-02-02", 175.0),
        (p2.id, "2026-03-02", 225.0),
        (p2.id, "2026-03-30", 260.0),
    ]
    for pid, date, val in points:
        service.create_measurement(
            conn, patient_id=pid, biomarker_name=biomarker,
            value=val, measured_at=date, modality="hormone", unit="ng/mL",
        )
    return p1, p2


def test_cohort_trajectories_basic_counts(conn):
    _seed_cohort(conn)
    result = analysis.cohort_trajectories(
        conn, peptide_name="CJC-1295", biomarker_name="Serum IGF-1"
    )
    assert result.n_patients == 2
    assert result.n_measurements == 6
    assert result.expected is not None
    assert result.expected["direction"] == "increase"


def test_cohort_trajectories_aligns_by_weeks(conn):
    _seed_cohort(conn)
    result = analysis.cohort_trajectories(
        conn, peptide_name="CJC-1295", biomarker_name="Serum IGF-1"
    )
    weeks = sorted(round(t.weeks_since_start, 1) for t in result.trajectories)
    # Each patient: ~0w, ~4w, ~8w → 6 points
    assert len(weeks) == 6
    assert weeks[0] < 1
    assert any(3 < w < 5 for w in weeks)
    assert any(7 < w < 9 for w in weeks)


def test_cohort_time_bins_compute_median(conn):
    _seed_cohort(conn)
    result = analysis.cohort_trajectories(
        conn, peptide_name="CJC-1295", biomarker_name="Serum IGF-1"
    )
    # Find the late bin and verify it captures the ~265 median
    late = [b for b in result.time_bins if 6 <= b.weeks_label <= 12]
    assert late, "expected a late time bin"
    assert 240 < late[0].median < 280


def test_dose_response_includes_pct_change(conn):
    _seed_cohort(conn)
    result = analysis.cohort_trajectories(
        conn, peptide_name="CJC-1295", biomarker_name="Serum IGF-1"
    )
    assert len(result.dose_response) == 1
    dr = result.dose_response[0]
    assert dr.dose == 2.0 and dr.dose_unit == "mg"
    assert dr.n_patients == 2
    assert dr.pct_change_from_baseline is not None
    assert dr.pct_change_from_baseline > 20  # IGF-1 should rise


def test_dose_filter(conn):
    _seed_cohort(conn)
    result = analysis.cohort_trajectories(
        conn, peptide_name="CJC-1295", biomarker_name="Serum IGF-1",
        dose_min=5.0,
    )
    assert result.n_measurements == 0


def test_available_biomarkers_marks_observed_count(conn):
    _seed_cohort(conn)
    panel = analysis.available_biomarkers(conn, "CJC-1295")
    assert panel, "expected CJC-1295 panel"
    by_name = {m["name"]: m for m in panel}
    assert by_name["Serum IGF-1"]["n_observed"] == 6
    # An unmeasured panel marker should be 0
    assert any(m["n_observed"] == 0 for m in panel)


def test_peptides_with_data(conn):
    _seed_cohort(conn)
    rows = analysis.peptides_with_data(conn)
    assert {r["peptide_name"]: r["n_patients"] for r in rows} == {"CJC-1295": 2}


def test_invalid_measured_at_is_skipped(conn):
    p = service.create_patient(conn, label="P")
    service.create_treatment(
        conn, patient_id=p.id, peptide_name="CJC-1295",
        dose=1.0, dose_unit="mg", start_date="2026-01-01",
    )
    service.create_measurement(
        conn, patient_id=p.id, biomarker_name="Serum IGF-1",
        value=200.0, measured_at="2026-02-30",  # invalid date
    )
    result = analysis.cohort_trajectories(
        conn, peptide_name="CJC-1295", biomarker_name="Serum IGF-1"
    )
    assert result.n_measurements == 0
