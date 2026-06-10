"""Authority/department registry.

Loaded from config/authorities.example.yaml. Mirrors RailMadad's department structure
(RPF, Medical, Sanitation, IRCTC Catering, Electrical, Operations, Commercial, Mechanical).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Authority:
    category: str
    department: str
    channel: str          # dispatch channel, e.g. "railmadad" | "email"


def load_authorities(config_path: str) -> list[Authority]:
    """Read the category -> authority mapping from YAML."""
    ...


def default_authority(config_path: str) -> Authority:
    """The fallback authority used when classification is unsure."""
    ...
