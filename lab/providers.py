"""Allowlisted lab-console providers. Keys stay in env / k8s secrets — never in git."""

from __future__ import annotations

import os
from typing import Any

# id → Hermes --provider flag, env key, models shown in the console.
PROVIDERS: dict[str, dict[str, Any]] = {
    "neuralwatt": {
        "label": "Neuralwatt",
        "hermes_provider": "custom:neuralwatt",
        "key_env": "NEURALWATT_API_KEY",
        "default_model": "glm-5.2-short-fast",
        "models": [
            "glm-5.2-short-fast",
            "glm-5.2-fast",
            "glm-5.2-short",
            "kimi-k2.6-fast",
            "qwen3.6-35b-fast",
        ],
    },
    "openai": {
        "label": "OpenAI",
        "hermes_provider": "custom:openai",
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o",
        "models": ["gpt-4o", "gpt-4.1", "gpt-4.1-mini", "o4-mini"],
    },
    "openrouter": {
        "label": "OpenRouter",
        "hermes_provider": "openrouter",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": "openai/gpt-4o",
        "models": [
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4",
            "google/gemini-2.5-flash",
        ],
    },
    "navigator": {
        "label": "NaviGator",
        "hermes_provider": "custom:navigator",
        "key_env": "NAVIGATOR_API_KEY",
        "default_model": "gemma-4-31b-it",
        "models": [
            "gemma-4-31b-it",
            "gemma-3-27b-it",
            "medgemma-27b-it",
            "llama-3.1-8b-instruct",
            "gpt-oss-20b",
        ],
    },
    "anthropic": {
        "label": "Anthropic",
        "hermes_provider": "anthropic",
        "key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-5",
        "models": [
            "claude-sonnet-4-5",
            "claude-opus-4-1",
            "claude-haiku-4-5-20251001",
        ],
    },
    "xai": {
        "label": "xAI",
        "hermes_provider": "xai",
        "key_env": "XAI_API_KEY",
        "default_model": "grok-4.6",
        "models": ["grok-4.6", "grok-4"],
    },
}

DEFAULT_PROVIDER = "neuralwatt"


def key_configured(provider_id: str) -> bool:
    spec = PROVIDERS.get(provider_id) or {}
    env_name = str(spec.get("key_env") or "")
    return bool(env_name and os.environ.get(env_name, "").strip())


def public_catalog() -> dict[str, Any]:
    rows = []
    for pid, spec in PROVIDERS.items():
        rows.append(
            {
                "id": pid,
                "label": spec["label"],
                "models": list(spec["models"]),
                "default_model": spec["default_model"],
                "key_configured": key_configured(pid),
            }
        )
    chosen = DEFAULT_PROVIDER if key_configured(DEFAULT_PROVIDER) else next(
        (p["id"] for p in rows if p["key_configured"]),
        DEFAULT_PROVIDER,
    )
    return {"providers": rows, "default_provider": chosen}


def resolve_turn(payload: dict[str, Any]) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    """Return ({provider_id, hermes_provider, model}, None) or (None, error_body)."""
    pid = str(payload.get("provider") or DEFAULT_PROVIDER).strip()
    spec = PROVIDERS.get(pid)
    if spec is None:
        return None, {"ok": False, "error": "unknown_provider", "provider": pid}
    model = str(payload.get("model") or spec["default_model"]).strip()
    allowed = {str(m) for m in spec["models"]}
    if model not in allowed:
        return None, {
            "ok": False,
            "error": "unknown_model",
            "provider": pid,
            "model": model,
        }
    if not key_configured(pid):
        return None, {"ok": False, "error": "key_not_configured", "provider": pid}
    return {
        "provider_id": pid,
        "hermes_provider": str(spec["hermes_provider"]),
        "model": model,
    }, None
