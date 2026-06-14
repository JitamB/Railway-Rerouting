"""Authority/department registry.

Loaded from config/authorities.example.yaml. Mirrors RailMadad's department structure
(RPF, Medical, Sanitation, IRCTC Catering, Electrical, Operations, Commercial, Mechanical).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

DEFAULT_CONFIG = str(Path(__file__).resolve().parent / "config" / "authorities.example.yaml")


@dataclass
class Authority:
    category: str
    department: str
    channel: str          # dispatch channel, e.g. "railmadad" | "email"


@lru_cache(maxsize=4)
def _load(config_path: str) -> dict:
    return yaml.safe_load(Path(config_path).read_text())


def load_authorities(config_path: str = DEFAULT_CONFIG) -> list[Authority]:
    """Read the category -> authority mapping from YAML."""
    data = _load(config_path)
    return [
        Authority(category=a["category"], department=a["department"], channel=a["channel"])
        for a in data.get("authorities", [])
    ]


def default_authority(config_path: str = DEFAULT_CONFIG) -> Authority:
    """The fallback authority used when classification is unsure."""
    d = _load(config_path).get("default", {})
    return Authority(
        category="general",
        department=d.get("department", "RailMadad General Helpdesk"),
        channel=d.get("channel", "railmadad"),
    )
