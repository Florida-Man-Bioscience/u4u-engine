"""Live regulatory source clients (Regulations.gov, ClinicalTrials.gov, openFDA, Federal Register)."""

from .regulations_gov import fetch_docket_summary
from .clinicaltrials import fetch_trials
from .openfda import fetch_openfda
from .federal_register import fetch_federal_register

__all__ = [
    "fetch_docket_summary",
    "fetch_trials",
    "fetch_openfda",
    "fetch_federal_register",
]
