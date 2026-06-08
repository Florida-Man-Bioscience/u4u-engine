"""
engine/regulatory
=================
FDA peptide regulatory status data and live-augmenting source clients.

Public interface
----------------
    build_dashboard_payload() -> dict     # curated + live, ready for /regulatory/peptides
    build_events_payload()    -> dict     # curated events + sources
"""

from .aggregator import build_dashboard_payload, build_events_payload

__all__ = ["build_dashboard_payload", "build_events_payload"]
