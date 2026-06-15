"""Seeded demo patients must be unmistakably labeled as non-real."""
import random

from engine.tracking import db, get_conn
from engine.tracking import service
from engine.tracking.seed import seed


def test_seed_labels_are_marked_demo():
    db.reset_initialized()
    with get_conn(":memory:") as conn:
        seed(conn, rng=random.Random(1), n_patients=3)
        labels = [p.label for p in service.list_patients(conn)]
        assert labels
        assert all(lbl.startswith("DEMO-") for lbl in labels)
