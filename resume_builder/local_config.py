from __future__ import annotations

import json
from pathlib import Path

from .models import LLMConfig


def load_local_llm_config(root: Path) -> LLMConfig:
    config_path = root / "local_settings.json"
    if not config_path.exists():
        return LLMConfig()

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    llm = payload.get("llm", {})
    return LLMConfig(
        model=llm.get("model", ""),
        base_url=llm.get("base_url", ""),
        api_key=llm.get("api_key", ""),
    )
