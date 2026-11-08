"""
Render the figures used in the README and report.

All visuals are rebuilt from the curated CSVs in ``data/`` so the repository can
be reproduced end to end. Outputs land in ``assets/figures/``.

Usage:
    python src/figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Polygon, Rectangle
from matplotlib.collections import PatchCollection

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GEO = ROOT / "geodata" / "nga_adm1.geojson"
FIG_DIR = ROOT / "assets" / "figures"

# ---------------------------------------------------------------- design tokens
INK = "#10231B"
MUTED = "#5C6F66"
GRID = "#DDE4DF"
PAGE = "#FFFFFF"
GREEN_DARK = "#12372A"
GREEN = "#2D6A4F"
GREEN_MID = "#52B788"
GREEN_LIGHT = "#B7E4C7"
GOLD = "#C9A227"
SAND = "#F6F1E4"

ZONE_COLORS = {
    "North West": "#12372A",
    "North Central": "#2D6A4F",
    "South West": "#C9A227",
    "South East": "#74C69D",
    "South South": "#8D6E63",
}

plt.rcParams.update(
    {
        "figure.facecolor": PAGE,
        "axes.facecolor": PAGE,
        "savefig.facecolor": PAGE,
        "font.family": "DejaVu Sans",
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": MUTED,
        "ytick.color": INK,
        "axes.edgecolor": GRID,
        "axes.linewidth": 0.8,
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.28,
    }
)


# ------------------------------------------------------------------- utilities
def load_disease_totals() -> list[tuple[str, int]]:
    import csv

    with (DATA / "disease_totals.csv").open(newline="", encoding="utf-8") as fh:
        rows = [(r["disease"], int(r["cases"])) for r in csv.DictReader(fh)]
    return sorted(rows, key=lambda r: r[1], reverse=True)


def load_states() -> list[dict]:
    import csv

    with (DATA / "covid19_by_state.csv").open(newline="", encoding="utf-8") as fh:
        out = []
        for r in csv.DictReader(fh):
            out.append(
                {
                    "state": r["state"],
                    "zone": r["geopolitical_zone"],
                    "cases": int(r["cases"]) if r["cases"] else None,
                }
            )
    return out


def titles(ax, title: str, subtitle: str | None = None) -> None:
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", color=INK, pad=18 if subtitle else 10)
    if subtitle:
        ax.text(
            0.0,
            1.015,
            subtitle,
            transform=ax.transAxes,
            fontsize=9.5,
            color=MUTED,
            va="bottom",
            ha="left",
        )


def footer(fig, text: str) -> None:
    fig.text(0.005, -0.005, text, fontsize=7.6, color=MUTED, va="top", ha="left")


def strip(ax, keep: str = "left") -> None:
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(side == keep)


def save(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / name)
    plt.close(fig)
    print(f"  wrote assets/figures/{name}")


SOURCE = "Source: Nigeria Disease Prevalence Dashboard (Power BI) · 10 states in scope"


# -------------------------------------------------------------------- figure 1
def fig_disease_burden() -> None:
    data = load_disease_totals()
    names = [d[0] for d in data][::-1]
    values = [d[1] for d in data][::-1]
    shades = [GREEN_LIGHT, GREEN_MID, GREEN, GREEN_DARK]
    ratio = data[0][1] / (sum(d[1] for d in data) - data[0][1])

    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    bars = ax.barh(names, values, color=shades, height=0.62, zorder=3)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + max(values) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,}",
            va="center",
            ha="left",
            fontsize=10.5,
            fontweight="bold",
            color=INK,
        )
    ax.set_xlim(0, max(values) * 1.16)
    ax.xaxis.set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=10.5)
    strip(ax, keep="left")
    ax.spines["left"].set_color(GRID)
    titles(
        ax,
        "Malaria carries two thirds of the recorded burden",
        "Cases recorded across the ten states in the dashboard",
    )
    ax.text(
        0.0,
        -0.14,
        f"Malaria alone equals {ratio:.1f}x the combined cases of flu, COVID-19 and TB.",
        transform=ax.transAxes,
        fontsize=8.6,
        color=MUTED,
    )
    footer(fig, SOURCE)
    save(fig, "fig01_disease_burden.png")


# -------------------------------------------------------------------- figure 2
def fig_disease_share() -> None:
    data = load_disease_totals()
    names = [d[0] for d in data]
    values = [d[1] for d in data]
    total = sum(values)
    colors = [GREEN_DARK, GREEN, GOLD, GREEN_LIGHT]

    fig, (ax, axl) = plt.subplots(
        1, 2, figsize=(8.6, 3.9), gridspec_kw={"width_ratios": [1, 1.05]}
    )
    ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.36, edgecolor=PAGE, linewidth=2.4),
    )
    ax.text(0, 0.13, f"{total:,}", ha="center", va="center", fontsize=18, fontweight="bold", color=INK)
    ax.text(0, -0.16, "total cases", ha="center", va="center", fontsize=9, color=MUTED)
    ax.set_aspect("equal")

    axl.axis("off")
    axl.set_xlim(0, 1)
    axl.set_ylim(0, 1)
    for i, (name, value, color) in enumerate(zip(names, values, colors)):
        y = 0.86 - i * 0.235
        axl.add_patch(Rectangle((0.0, y - 0.032), 0.045, 0.064, color=color, clip_on=False))
        axl.text(0.085, y, name, fontsize=11, fontweight="bold", color=INK, va="center")
        axl.text(
            0.085,
            y - 0.085,
            f"{value:,} cases · {value / total * 100:.1f}% of total",
            fontsize=9,
            color=MUTED,
            va="center",
        )

    fig.text(
        0.02,
        0.99,
        "Share of total recorded cases",
        fontsize=14,
        fontweight="bold",
        color=INK,
        va="top",
        ha="left",
    )
    fig.text(
        0.02,
        0.915,
        "Malaria accounts for just over two thirds of all recorded cases",
        fontsize=9.2,
        color=MUTED,
        va="top",
        ha="left",
    )
    fig.subplots_adjust(top=0.80, bottom=0.10)
    footer(fig, SOURCE)
    save(fig, "fig02_disease_share.png")


# -------------------------------------------------------------------- figure 3
def fig_state_ranking() -> None:
    states = [s for s in load_states() if s["cases"] is not None]
    states.sort(key=lambda s: s["cases"])
    names = [s["state"] for s in states]
    values = [s["cases"] for s in states]
    colors = [ZONE_COLORS[s["zone"]] for s in states]

    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    bars = ax.barh(names, values, color=colors, height=0.66, zorder=3)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + max(values) * 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,}",
            va="center",
            ha="left",
            fontsize=9.6,
            fontweight="bold",
            color=INK,
        )
    ax.set_xlim(0, max(values) * 1.15)
    ax.xaxis.set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=10)
    strip(ax, keep="left")
    ax.spines["left"].set_color(GRID)
    titles(
        ax,
        "COVID-19 concentrates in Kano, Kaduna and the FCT",
        "Published COVID-19 cases by state, coloured by geopolitical zone",
    )

    handles = [
        Rectangle((0, 0), 1, 1, color=c)
        for c in ZONE_COLORS.values()
        if c in colors
    ]
    labels = [z for z in ZONE_COLORS if ZONE_COLORS[z] in colors]
    ax.legend(
        handles,
        labels,
        loc="lower right",
        frameon=False,
        fontsize=8.4,
        handlelength=1.0,
        handleheight=0.8,
        borderaxespad=0.2,
        labelcolor=MUTED,
    )
    ax.text(
        0.0,
        -0.13,
        "Oyo appears in the dashboard state filter but no case value was published, so it is omitted.",
        transform=ax.transAxes,
        fontsize=8.2,
        color=MUTED,
    )
    footer(fig, SOURCE)
    save(fig, "fig03_covid19_by_state.png")


# -------------------------------------------------------------------- figure 4
def fig_choropleth() -> None:
    geo = json.loads(GEO.read_text())
    states = {s["state"]: s for s in load_states()}
    alias = {"Abuja Federal Capital Territory": "Abuja (FCT)"}

    values = {k: v["cases"] for k, v in states.items() if v["cases"] is not None}
    cmap = LinearSegmentedColormap.from_list(
        "prevalence", ["#EAF4EC", GREEN_LIGHT, GREEN_MID, GREEN, GREEN_DARK]
    )
    norm = Normalize(vmin=0, vmax=max(values.values()))

    fig, ax = plt.subplots(figsize=(6.6, 5.7))
    study_patches, study_vals, study_labels = [], [], []
    other = []

    for feature in geo["features"]:
        name = alias.get(feature["properties"]["shapeName"], feature["properties"]["shapeName"])
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            ring = poly[0]
            if name in values:
                study_patches.append(Polygon(ring, closed=True))
                study_vals.append(values[name])
                study_labels.append((name, ring))
            else:
                other.append(Polygon(ring, closed=True))

    ax.add_collection(
        PatchCollection(other, facecolor="#F0F0EC", edgecolor="#B9C2BB", linewidth=0.35, zorder=1)
    )
    coll = PatchCollection(
        study_patches, cmap=cmap, norm=norm, edgecolor="#12372A", linewidth=0.7, zorder=2
    )
    coll.set_array([v for v in study_vals])
    ax.add_collection(coll)

    for name, ring in study_labels:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        ax.text(
            cx,
            cy,
            name.replace(" (FCT)", "\n(FCT)"),
            fontsize=6.4,
            ha="center",
            va="center",
            color="#0B1F17",
            linespacing=1.0,
            path_effects=[pe.withStroke(linewidth=2.2, foreground="white", alpha=0.85)],
            zorder=4,
        )

    ax.set_xlim(2.45, 14.95)
    ax.set_ylim(4.0, 13.95)
    ax.set_aspect("equal")
    ax.axis("off")

    cbar = fig.colorbar(coll, ax=ax, orientation="horizontal", fraction=0.038, pad=0.02, aspect=42)
    cbar.set_label("Published COVID-19 cases", fontsize=8.6, color=MUTED)
    cbar.ax.tick_params(labelsize=7.6, color=MUTED)
    cbar.outline.set_visible(False)

    fig.text(
        0.02,
        0.99,
        "Geographic spread of published COVID-19 cases",
        va="top",
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.02,
        0.925,
        "Ten states under review; grey areas lie outside the dashboard scope",
        fontsize=9.2,
        color=MUTED,
        va="top",
        ha="left",
    )
    fig.subplots_adjust(top=0.855, bottom=0.115)
    footer(fig, "Source: Nigeria Disease Prevalence Dashboard · Boundaries: geoBoundaries / GRID3 (CC BY 4.0)")
    save(fig, "fig04_covid19_choropleth.png")


# -------------------------------------------------------------------- figure 5
def fig_reconciliation() -> None:
    states = [s for s in load_states() if s["cases"] is not None]
    published = sum(s["cases"] for s in states)
    kpi = 5400

    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    labels = ["Dashboard KPI card", "Sum of published\nstate-level figures"]
    values = [kpi, published]
    colors = [GREEN_DARK, GOLD]
    bars = ax.barh(labels, values, color=colors, height=0.40, zorder=3)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + published * 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,}",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=INK,
        )
    ax.set_xlim(0, published * 1.16)
    ax.xaxis.set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=10)
    strip(ax, keep="left")
    ax.spines["left"].set_color(GRID)
    ax.set_ylim(-0.55, 1.55)
    fig.text(
        0.02,
        0.985,
        "State labels do not reconcile with the KPI card",
        fontsize=14.5,
        fontweight="bold",
        color=INK,
        va="top",
        ha="left",
    )
    fig.text(
        0.02,
        0.855,
        f"Published state figures total {published:,} against a headline of {kpi:,} COVID-19 cases",
        fontsize=9.2,
        color=MUTED,
        va="top",
        ha="left",
    )
    fig.subplots_adjust(top=0.70, bottom=0.16, left=0.24)
    footer(fig, SOURCE)
    save(fig, "fig05_reconciliation.png")


def main() -> None:
    print("Rendering figures...")
    fig_disease_burden()
    fig_disease_share()
    fig_state_ranking()
    fig_choropleth()
    fig_reconciliation()
    print("Done.")


if __name__ == "__main__":
    main()
