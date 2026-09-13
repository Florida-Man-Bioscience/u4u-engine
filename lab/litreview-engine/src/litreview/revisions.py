"""Revision comparison for numeric versions and content hashes."""

from __future__ import annotations

from typing import Any


def revision_matches(left: Any, right: Any) -> bool:
    """Compare integer revisions numerically, otherwise compare their strings."""
    if left is None or right is None or left == "" or right == "":
        return False
    try:
        return int(left) == int(right)
    except (TypeError, ValueError):
        return str(left) == str(right)
