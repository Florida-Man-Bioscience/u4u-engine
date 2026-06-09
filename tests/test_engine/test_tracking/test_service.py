from engine.tracking import service


def test_patient_crud(conn):
    p = service.create_patient(conn, label="P-001", sex="M", birth_year=1990)
    assert p.label == "P-001"
    assert service.get_patient(conn, p.id).id == p.id
    assert [x.label for x in service.list_patients(conn)] == ["P-001"]
    assert service.delete_patient(conn, p.id) is True
    assert service.get_patient(conn, p.id) is None


def test_treatment_links_to_patient(conn):
    p = service.create_patient(conn, label="P-002")
    t = service.create_treatment(
        conn,
        patient_id=p.id,
        peptide_name="BPC-157",
        start_date="2026-01-01",
        dose=250.0,
        dose_unit="mcg",
        schedule="BID",
        route="SC",
    )
    assert t.peptide_name == "BPC-157"
    by_patient = service.list_treatments_for_patient(conn, p.id)
    assert [x.id for x in by_patient] == [t.id]
    by_peptide = service.list_treatments_by_peptide(conn, "BPC-157")
    assert [x.id for x in by_peptide] == [t.id]


def test_cascade_delete_patient_removes_treatments_and_measurements(conn):
    p = service.create_patient(conn, label="P-003")
    t = service.create_treatment(
        conn, patient_id=p.id, peptide_name="MOTS-c", start_date="2026-01-01"
    )
    service.create_measurement(
        conn,
        patient_id=p.id,
        treatment_id=t.id,
        biomarker_name="HOMA-IR",
        value=2.5,
        measured_at="2026-01-15",
    )
    assert service.delete_patient(conn, p.id) is True
    assert service.list_treatments_for_patient(conn, p.id) == []
    assert service.list_measurements_for_patient(conn, p.id) == []


def test_measurement_filter_by_biomarker(conn):
    p = service.create_patient(conn, label="P-004")
    service.create_measurement(
        conn, patient_id=p.id, biomarker_name="Serum IGF-1",
        value=200.0, measured_at="2026-01-01",
    )
    service.create_measurement(
        conn, patient_id=p.id, biomarker_name="Serum IGF-1",
        value=240.0, measured_at="2026-02-01",
    )
    service.create_measurement(
        conn, patient_id=p.id, biomarker_name="ALT",
        value=22.0, measured_at="2026-02-01",
    )
    igf = service.list_measurements_for_patient(conn, p.id, biomarker_name="Serum IGF-1")
    assert [m.value for m in igf] == [200.0, 240.0]


def test_csv_parses_valid_rows_and_reports_errors(conn):
    p = service.create_patient(conn, label="P-005")
    csv_text = (
        "patient_id,biomarker_name,value,measured_at,unit\n"
        f"{p.id},Serum IGF-1,210,2026-01-01,ng/mL\n"
        f"{p.id},Serum IGF-1,not-a-number,2026-02-01,ng/mL\n"
        f"{p.id},ALT,25,2026-02-01,U/L\n"
    )
    records, errors = service.parse_measurement_csv(csv_text)
    assert len(records) == 2
    assert len(errors) == 1
    assert "row 3" in errors[0]


def test_csv_missing_required_column(conn):
    csv_text = "patient_id,biomarker_name,measured_at\n1,IGF,2026-01-01\n"
    records, errors = service.parse_measurement_csv(csv_text)
    assert records == []
    assert any("value" in e for e in errors)
