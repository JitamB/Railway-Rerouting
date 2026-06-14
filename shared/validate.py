"""Contract validation harness — proves the sample fixtures match the frozen schemas.

Run:  python shared/validate.py
This is the Step-1 "Verify" check: every sample in schemas/examples/ validates against its
schema, and a few deliberately-bad payloads are correctly rejected, so we know the contracts
actually constrain what crosses a service boundary.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMAS_DIR = Path(__file__).parent / "schemas"
EXAMPLES_DIR = SCHEMAS_DIR / "examples"

# (schema file, valid sample file)
PAIRS = [
    ("events.schema.json", "event.sample.json"),
    ("prediction.schema.json", "prediction.sample.json"),
    ("grievance.schema.json", "grievance.sample.json"),
]

# (schema file, bad payload, what should trip it) — proves the constraints bite.
NEGATIVES = [
    ("events.schema.json", {"train_no": "1", "station": "X", "delay_min": 0,
                            "received_time": "2026-01-01T00:00:00+05:30", "source": "twin"},
     "missing required event_time"),
    ("events.schema.json", {"train_no": "1", "station": "X", "delay_min": 0, "source": "rtis_x",
                            "event_time": "2026-01-01T00:00:00+05:30",
                            "received_time": "2026-01-01T00:00:00+05:30"},
     "source not in enum"),
    ("prediction.schema.json", {"station": "X", "cascade_risk": 1.4,
                                "delay_interval_min": [1, 2], "data_age_s": 0, "mode": "live"},
     "cascade_risk > 1"),
    ("prediction.schema.json", {"station": "X", "cascade_risk": 0.5,
                                "delay_interval_min": [1, 2], "data_age_s": 0, "mode": "guess"},
     "mode not in enum"),
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    failures = 0

    print("== validating sample fixtures ==")
    for schema_file, sample_file in PAIRS:
        validator = Draft202012Validator(_load(SCHEMAS_DIR / schema_file))
        errors = sorted(validator.iter_errors(_load(EXAMPLES_DIR / sample_file)), key=str)
        if errors:
            failures += 1
            print(f"  FAIL  {sample_file} -> {schema_file}")
            for e in errors:
                print(f"        {e.message}")
        else:
            print(f"  PASS  {sample_file} -> {schema_file}")

    print("== confirming bad payloads are rejected ==")
    for schema_file, bad, reason in NEGATIVES:
        validator = Draft202012Validator(_load(SCHEMAS_DIR / schema_file))
        if validator.is_valid(bad):
            failures += 1
            print(f"  FAIL  {schema_file}: accepted invalid payload ({reason})")
        else:
            print(f"  PASS  {schema_file}: rejected ({reason})")

    print(f"\n{'ALL CONTRACTS LOCKED' if not failures else f'{failures} FAILURE(S)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
