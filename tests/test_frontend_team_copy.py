"""Public /team copy contract.

t-fmbweb-team-implement: do not invent bios. Titles for the six
founders must match operator-approved public roles. Narrative blurbs
wait on t-fmbweb-team-bios (still open — no written OK).
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

# flmanbiosci-ops team-assets.md / product-naming.md — do not invent.
APPROVED_FOUNDER_ROLES = {
    "noah": "Founder & CEO",
    "garrett": "Founder",
    "curtis": "Chief Vision Officer & CPO of PeptOdyssey",
    "michael": "Chemistry & Delivery",
    "jacob": "Bioinformatics",
    "tyler": "Clinical & Operations",
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


def test_no_invented_bios() -> None:
    """Blurbs require written OK from t-fmbweb-team-bios. Until then: empty."""
    members = _members()
    assert members, "failed to parse any team members from team.ts"
    invented = {
        slug: m["blurb"]
        for slug, m in members.items()
        if m["blurb"].strip()
    }
    assert invented == {}, f"unapproved bios on public roster: {invented}"
