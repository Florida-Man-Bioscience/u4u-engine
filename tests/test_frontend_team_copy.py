"""Public /team copy contract.

Locks founder roles and roster blurbs to the live SSoT in
frontend/src/lib/team.ts. New or rewritten bios still fail until this
snapshot is updated with the copy.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM_TS = ROOT / "frontend" / "src" / "lib" / "team.ts"
TEAM_PAGE = ROOT / "frontend" / "src" / "app" / "(marketing)" / "team" / "page.tsx"
HOME_PAGE = ROOT / "frontend" / "src" / "app" / "(marketing)" / "page.tsx"
CHROME = ROOT / "frontend" / "src" / "components" / "CompanyChrome.tsx"

# Live public roles on team.ts (2026 Activator roster).
APPROVED_FOUNDER_ROLES = {
    "noah": "Founder & CEO",
    "garrett": "Co-founder · Omics",
    "curtis": "Co-founder · PeptOdyssey",
    "michael": "Co-founder · Structural biology",
    "jacob": "Founder · Bioinformatics",
    "tyler": "Founder · Clinical & operations",
}

# Shipped blurbs. Drift here is a copy change, not an invention to ignore.
APPROVED_BLURBS = {
    "noah": "Builds the engine and app foundations. Bioinformatics, pipeline architecture, and company operations.",
    "curtis": "Builds the PeptOdyssey engine and the clinician-facing product surface.",
    "garrett": "Calcium-sensing and transmembrane proteins; metabolism and mitochondria-focused science.",
    "michael": "Structural biochemistry and the VR structural-biochemistry platform.",
    "jacob": "Bioinformatics and immunology.",
    "tyler": "Clinical and operations; skunkworks and program execution.",
    "sasank": "MD/PhD student, University of Florida. Clinical link and PeptOdyssey engine contributor.",
    "kayla": "MD-PhD student, University of Miami. Safety / contraindication layer for genotype-aware peptide protocols.",
    "rocky": "Post-doc, Moffitt Cancer Center. Oncology genetics advisor; VR structural biochemistry project lead.",
    "min": "Metabolism, adipose biology, and nutrition. Nucleate Activator contributor.",
    "delaney": "Clinical and public-health researcher guiding clinical and translational strategy.",
    "christopher": "Joined the 2026 Nucleate Activator cohort mid-program.",
    "hampton": "Graduate student, MTSU. Engineering lead for platform and infrastructure.",
    "jeran": "GTM and growth; channel and go-to-market execution.",
    "ty": "Non-founder contributor supporting company operations and growth.",
    "giuseppina": "Founder & CEO, Auralis Biotech. Commercialization and strategic partnership advisor.",
}

MEMBER_RE = re.compile(
    r"id:\s*\"(?P<id>[^\"]+)\"\s*,\s*"
    r"name:\s*\"(?P<name>[^\"]+)\"\s*,\s*"
    r"role:\s*\"(?P<role>[^\"]+)\"\s*,\s*"
    r"blurb:\s*(?P<blurb>\"(?:[^\"\\]|\\.)*\")",
    re.S,
)


def _members() -> dict[str, dict[str, str]]:
    src = TEAM_TS.read_text(encoding="utf-8")
    out: dict[str, dict[str, str]] = {}
    for m in MEMBER_RE.finditer(src):
        out[m.group("id")] = {
            "name": m.group("name"),
            "role": m.group("role"),
            "blurb": ast.literal_eval(m.group("blurb")),
        }
    return out


def test_team_roster_file_exists() -> None:
    assert TEAM_TS.is_file()
    assert TEAM_PAGE.is_file()


def test_homepage_and_chrome_link_to_team() -> None:
    assert 'href="/team"' in HOME_PAGE.read_text(encoding="utf-8")
    assert 'href="/team"' in CHROME.read_text(encoding="utf-8")


def test_founder_public_roles_match_approved_copy() -> None:
    members = _members()
    missing = set(APPROVED_FOUNDER_ROLES) - set(members)
    assert not missing, f"missing founders in team.ts: {sorted(missing)}"
    for slug, role in APPROVED_FOUNDER_ROLES.items():
        assert members[slug]["role"] == role, (
            f"{slug} public role {members[slug]['role']!r} != approved {role!r}"
        )


def test_public_bios_match_approved_copy() -> None:
    members = _members()
    assert members, "failed to parse any team members from team.ts"
    live = {slug: m["blurb"] for slug, m in members.items()}
    extra = set(live) - set(APPROVED_BLURBS)
    missing = set(APPROVED_BLURBS) - set(live)
    assert not extra, f"unapproved roster ids: {sorted(extra)}"
    assert not missing, f"missing roster ids: {sorted(missing)}"
    drift = {
        slug: (APPROVED_BLURBS[slug], live[slug])
        for slug in APPROVED_BLURBS
        if live[slug] != APPROVED_BLURBS[slug]
    }
    assert drift == {}, f"blurb drift vs approved snapshot: {drift}"
