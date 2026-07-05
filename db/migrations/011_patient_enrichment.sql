-- Wave 3b: per-patient pipeline enrichment.
--
-- The PRS-inflammatory and BPC-157 responder feature adapters read
-- ``ResponderContext.extra["prs_profile"]`` / ``["bpc157"]`` — signals that are
-- computed over the full annotated genome by the /analyze pipeline but are NOT
-- stored in the ~25-SNP tracking GeneticProfile, so they cannot be recomputed at
-- predict time. This table persists them once, at
-- ``POST /tracking/patients/from-job`` (where the full job results still exist),
-- so predict_response can thread them into the responder context and the
-- adapters actually fire. Absent rows are a graceful no-op (adapters contribute
-- nothing), so existing patients are unaffected.
CREATE TABLE IF NOT EXISTS patient_enrichment (
    patient_id      TEXT        PRIMARY KEY REFERENCES patients(id) ON DELETE CASCADE,
    enrichment_json TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
