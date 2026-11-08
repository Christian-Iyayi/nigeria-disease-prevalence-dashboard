"""
Compute headline metrics for the Nigeria Disease Prevalence Dashboard.

Reads the curated CSVs in ``data/`` and writes machine-readable metrics plus a
short Markdown summary to ``outputs/``.

Usage:
    python src/analysis.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"


def load_disease_totals() -> list[dict]:
    with (DATA / "disease_totals.csv").open(newline="", encoding="utf-8") as fh:
        return [
            {"disease": row["disease"], "cases": int(row["cases"])}
            for row in csv.DictReader(fh)
        ]


def load_state_cases() -> list[dict]:
    with (DATA / "covid19_by_state.csv").open(newline="", encoding="utf-8") as fh:
        rows = []
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "state": row["state"],
                    "zone": row["geopolitical_zone"],
                    "cases": int(row["cases"]) if row["cases"] else None,
                    "source": row["source"],
                    "confidence": row["confidence"],
                }
            )
        return rows


def build_metrics() -> dict:
    diseases = sorted(load_disease_totals(), key=lambda r: r["cases"], reverse=True)
    states = load_state_cases()

    total = sum(d["cases"] for d in diseases)
    for d in diseases:
        d["share_of_total_pct"] = round(d["cases"] / total * 100, 2)

    leader, runner_up = diseases[0], diseases[1]
    others = total - leader["cases"]

    reported = [s for s in states if s["cases"] is not None]
    ranked = sorted(reported, key=lambda s: s["cases"], reverse=True)

    by_zone: dict[str, int] = {}
    for s in reported:
        by_zone[s["zone"]] = by_zone.get(s["zone"], 0) + s["cases"]

    return {
        "diseases": diseases,
        "total_cases_all_diseases": total,
        "disease_classes": len(diseases),
        "malaria_share_pct": leader["share_of_total_pct"],
        "malaria_vs_rest_ratio": round(leader["cases"] / others, 2),
        "runner_up": runner_up,
        "states_in_scope": len(states),
        "states_with_published_value": len(reported),
        "states_missing_value": [s["state"] for s in states if s["cases"] is None],
        "covid_state_values_sum": sum(s["cases"] for s in reported),
        "covid_kpi_total": next(d["cases"] for d in diseases if d["disease"] == "COVID-19"),
        "covid_top5": ranked[:5],
        "covid_lowest": ranked[-3:],
        "covid_by_zone": dict(sorted(by_zone.items(), key=lambda kv: kv[1], reverse=True)),
        "notes": [
            "Totals for Malaria, Flu, COVID-19 and Tuberculosis come from the dashboard KPI cards and are internally consistent.",
            "State-level COVID-19 figures do not sum to the 5,400 KPI card; treat the state values as a relative ranking, not an absolute count.",
            "Oyo is present in the dashboard state filter but no case value was published for it.",
        ],
    }


def render_markdown(metrics: dict) -> str:
    lines = ["# Generated metrics", "", "Produced by `src/analysis.py`. Do not edit by hand.", ""]
    lines += ["## Disease burden (10 states in scope)", ""]
    lines += ["| Disease | Cases | Share of total |", "| --- | ---: | ---: |"]
    for d in metrics["diseases"]:
        lines.append(f"| {d['disease']} | {d['cases']:,} | {d['share_of_total_pct']}% |")
    lines.append(f"| **Total** | **{metrics['total_cases_all_diseases']:,}** | 100% |")
    lines += ["", "## COVID-19 by state", ""]
    lines += ["| Rank | State | Zone | Cases |", "| ---: | --- | --- | ---: |"]
    ordered = sorted(
        [s for s in metrics["covid_top5"]] , key=lambda s: s["cases"], reverse=True
    )
    for i, s in enumerate(ordered, 1):
        lines.append(f"| {i} | {s['state']} | {s['zone']} | {s['cases']:,} |")
    lines += ["", "## Coverage and caveats", ""]
    lines.append(
        f"- States with a published COVID-19 value: {metrics['states_with_published_value']} of {metrics['states_in_scope']}"
    )
    lines.append(f"- States without a published value: {', '.join(metrics['states_missing_value'])}")
    lines.append(
        f"- Sum of published state figures ({metrics['covid_state_values_sum']:,}) vs. dashboard KPI card ({metrics['covid_kpi_total']:,})"
    )
    lines += ["", "See `docs/data_notes.md` for the full reconciliation notes."]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    metrics = build_metrics()
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (OUT / "metrics.md").write_text(render_markdown(metrics), encoding="utf-8")
    print(f"Total cases across four diseases: {metrics['total_cases_all_diseases']:,}")
    print(f"Malaria share: {metrics['malaria_share_pct']}%")
    print(f"Wrote {OUT/'metrics.json'} and {OUT/'metrics.md'}")


if __name__ == "__main__":
    main()
