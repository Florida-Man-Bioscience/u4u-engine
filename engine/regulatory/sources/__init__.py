"""Live regulatory source clients (Regulations.gov, ClinicalTrials.gov, openFDA, Federal Register)."""

from .clinicaltrials import fetch_trials
from .federal_register import fetch_federal_register
from .openfda import fetch_openfda
from .regulations_gov import fetch_docket_summary

__all__ = [
    "fetch_docket_summary",
    "fetch_trials",
    "fetch_openfda",
    "fetch_federal_register",
]
