"""
Integrity checks for the curated datasets.

Standard library only, so it can run in CI with no install step.

Usage:
    python src/validate.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GEO = ROOT / "geodata" / "nga_adm1.geojson"

TOTAL_COLUMNS = ["disease", "cases"]
STATE_COLUMNS = [
    "state",
    "geopolitical_zone",
    "cases",
    "source",
    "confidence",
    "note",
]
ZONES = {
    "North Central",
    "North East",
    "North West",
    "South East",
    "South South",
    "South West",
}
EXPECTED_STATES = 10
EXPECTED_DISEASES = {"Malaria", "Flu", "COVID-19", "Tuberculosis"}
GEO_ALIASES = {"Abuja (FCT)": "Abuja Federal Capital Territory"}

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read_csv(path: Path, expected_columns: list[str]) -> list[dict]:
    check(path.exists(), f"missing file: {path.relative_to(ROOT)}")
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        check(
            reader.fieldnames == expected_columns,
            f"{path.name}: expected columns {expected_columns}, found {reader.fieldnames}",
        )
        return list(reader)


def main() -> int:
    totals = read_csv(DATA / "disease_totals.csv", TOTAL_COLUMNS)
    states = read_csv(DATA / "covid19_by_state.csv", STATE_COLUMNS)

    # --- disease totals -----------------------------------------------------
    names = {row["disease"] for row in totals}
    check(names == EXPECTED_DISEASES, f"disease names changed: {sorted(names)}")
    total_cases = 0
    for row in totals:
        try:
            value = int(row["cases"])
        except (TypeError, ValueError):
            errors.append(f"non-integer case count for {row['disease']}: {row['cases']!r}")
            continue
        check(value > 0, f"non-positive case count for {row['disease']}")
        total_cases += value
    check(total_cases == 105_620, f"total cases changed: {total_cases:,} (expected 105,620)")

    # --- state table --------------------------------------------------------
    check(len(states) == EXPECTED_STATES, f"expected {EXPECTED_STATES} states, found {len(states)}")
    seen: set[str] = set()
    for row in states:
        state = row["state"]
        check(state not in seen, f"duplicate state: {state}")
        seen.add(state)
        check(row["geopolitical_zone"] in ZONES, f"unknown zone for {state}: {row['geopolitical_zone']}")
        check(row["confidence"] in {"High", "Medium", "Low"}, f"bad confidence for {state}")
        if row["cases"]:
            try:
                check(int(row["cases"]) > 0, f"non-positive cases for {state}")
            except ValueError:
                errors.append(f"non-integer cases for {state}: {row['cases']!r}")
        else:
            check(
                row["source"] == "Not reported",
                f"{state} has no cases but source is {row['source']!r}",
            )
        check(
            bool(row["note"]) or row["confidence"] == "High",
            f"{state} is not High confidence but carries no explanatory note",
        )

    # --- geography ----------------------------------------------------------
    if GEO.exists():
        geo_names = {
            feature["properties"]["shapeName"]
            for feature in json.loads(GEO.read_text())["features"]
        }
        for row in states:
            target = GEO_ALIASES.get(row["state"], row["state"])
            check(target in geo_names, f"state missing from geodata: {row['state']}")
    else:
        errors.append("missing geodata/nga_adm1.geojson")

    if errors:
        print(f"{len(errors)} problem(s) found:\n")
        for problem in errors:
            print(f"  - {problem}")
        return 1

    print("All checks passed.")
    print(f"  diseases: {len(totals)}  states: {len(states)}  total cases: {total_cases:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
