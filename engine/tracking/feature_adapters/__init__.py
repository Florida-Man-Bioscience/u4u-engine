"""
engine/tracking/feature_adapters/
=================================
Auto-discovering registry of responder feature adapters.

Every submodule in this package is imported on package load so that adapters
decorated with ``@register_adapter`` self-register. A Phase-1 fan-out unit
adds a new adapter simply by dropping a ``*_adapter.py`` file here — **no edit
to any shared file is required**.

The genetics adapter (``genetics_adapter.py``) is the anchored reference
feature and ships first.
"""
from __future__ import annotations

import importlib
import pkgutil


def _discover() -> None:
    for mod in pkgutil.iter_modules(__path__):
        if mod.name.startswith("_"):
            continue
        importlib.import_module(f"{__name__}.{mod.name}")


_discover()
