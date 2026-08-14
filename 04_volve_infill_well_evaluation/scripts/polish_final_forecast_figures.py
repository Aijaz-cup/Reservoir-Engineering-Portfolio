from pathlib import Path
from datetime import datetime
import csv
import math

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# =====================================================================
# PROJECT 04 — FINAL FIGURE POLISH
#
# IMPORTANT:
# This script changes presentation only.
# It does NOT change simulation results or extracted numerical data.
# =====================================================================

REPO = Path(
    "/mnt/c/Users/ADMIN/Desktop/GitHub/"
    "Reservoir-Engineering-Portfolio/"
    "04_volve_infill_well_evaluation"
)

RESULTS = REPO / "results"
FIGDIR = REPO / "figures" / "final"
DOCS = REPO / "docs"

TS_FILE = RESULTS / "final_forecast_timeseries.csv"
CMP_FILE = RESULTS / "final_forecast_comparison.csv"

FIGDIR.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# Fixed visual identity
#
# Same candidate gets same color in every plot.
# ---------------------------------------------------------------------

COLORS = {
    "BASE": "#6f6f6f",
    "A": "#1f77b4",
    "B": "#ff7f0e",
    "C": "#2ca02c",
}

LABELS = {
    "BASE": "BASE",
    "A": "Candidate A",
    "B": "Candidate B",
    "C": "Candidate C",
}


def num(x):
    try:
        x = float(x)
        return x if math.isfinite(x) else float("nan")
    except Exception:
        return float("nan")


def dt(x):
    return datetime.strptime(x, "%Y-%m-%d")


def load_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def save(fig, stem):
    png = FIGDIR / f"{stem}.png"
    pdf = FIGDIR / f"{stem}.pdf"

    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight"
    )

    fig.savefig(
        pdf,
        bbox_inches="tight"
    )

    plt.close(fig)

    print("WROTE:", png)
    print("WROTE:", pdf)


def format_date_axis(ax):
    ax.xaxis.set_major_locator(
        mdates.YearLocator()
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )


def active_rows(rows):
    """
    Keep only report dates where the candidate is actually producing.

    This prevents the pre-opening 2016 zero from being interpreted as
    a physical 0% water cut or a meaningful producing rate.
    """

    selected = []

    for r in rows:

        qo = num(r["WOPR"])
        qw = num(r["WWPR"])

        if (
            math.isfinite(qo)
            and math.isfinite(qw)
            and abs(qo) + abs(qw) > 1.0e-8
        ):
            selected.append(r)

    return selected


timeseries = load_csv(TS_FILE)
comparison = load_csv(CMP_FILE)

by_case = {}

for case in ["BASE", "A", "B", "C"]:

    rows = [
        r for r in timeseries
        if r["case"] == case
    ]

    rows.sort(
        key=lambda r: r["date"]
    )

    by_case[case] = rows


cmp = {
    r["case"]: r
    for r in comparison
}


# =====================================================================
# FIGURE 07 — CUMULATIVE OIL
# =====================================================================

fig, ax = plt.subplots(
    figsize=(9.0, 5.6)
)

for case in ["BASE", "A", "B", "C"]:

    rows = by_case[case]

    dates = [
        dt(r["date"])
        for r in rows
    ]

    fopt = [
        num(r["FOPT"])
        for r in rows
    ]

    start = fopt[0]

    cumulative = [
        (v - start) / 1000.0
        for v in fopt
    ]

    ax.plot(
        dates,
        cumulative,
        marker="o",
        linewidth=2.0,
        markersize=4,
        color=COLORS[case],
        label=LABELS[case]
    )


ax.set_title(
    "Standalone Infill Screening — Five-Year Cumulative Oil"
)

ax.set_xlabel(
    "Forecast date"
)

ax.set_ylabel(
    "Forecast cumulative oil (10³ Sm³)"
)

ax.grid(
    True,
    alpha=0.25
)

format_date_axis(ax)

ax.legend(
    loc="center left",
    bbox_to_anchor=(1.01, 0.5)
)

fig.subplots_adjust(
    right=0.79
)

save(
    fig,
    "07_forecast_cumulative_oil"
)


# =====================================================================
# FIGURE 08 — OIL-RATE RESPONSE
#
# Remove pre-opening zero point.
# =====================================================================

fig, ax = plt.subplots(
    figsize=(9.0, 5.6)
)

for case in ["A", "B", "C"]:

    rows = active_rows(
        by_case[case]
    )

    dates = [
        dt(r["date"])
        for r in rows
    ]

    rates = [
        num(r["WOPR"])
        for r in rows
    ]

    ax.plot(
        dates,
        rates,
        marker="o",
        linewidth=2.0,
        markersize=4,
        color=COLORS[case],
        label=LABELS[case]
    )


ax.set_title(
    "Standalone Infill Screening — Candidate Oil-Rate Response"
)

ax.set_xlabel(
    "Forecast date"
)

ax.set_ylabel(
    "Oil production rate (Sm³/day)"
)

ax.set_ylim(
    bottom=0
)

ax.grid(
    True,
    alpha=0.25
)

format_date_axis(ax)

ax.legend(
    loc="center left",
    bbox_to_anchor=(1.01, 0.5)
)

fig.subplots_adjust(
    right=0.79
)

save(
    fig,
    "08_candidate_oil_rate"
)


# =====================================================================
# FIGURE 09 — WATER CUT
#
# CRITICAL:
# Do NOT plot inactive 2016 zero values.
# =====================================================================

fig, ax = plt.subplots(
    figsize=(9.0, 5.6)
)

for case in ["A", "B", "C"]:

    rows = active_rows(
        by_case[case]
    )

    dates = [
        dt(r["date"])
        for r in rows
    ]

    water_cut = [
        100.0 * num(r["WWCT"])
        for r in rows
    ]

    ax.plot(
        dates,
        water_cut,
        marker="o",
        linewidth=2.0,
        markersize=4,
        color=COLORS[case],
        label=LABELS[case]
    )


ax.set_title(
    "Standalone Infill Screening — Candidate Water-Cut Evolution"
)

ax.set_xlabel(
    "Forecast date"
)

ax.set_ylabel(
    "Water cut (%)"
)

ax.set_ylim(
    0,
    105
)

ax.grid(
    True,
    alpha=0.25
)

format_date_axis(ax)

ax.legend(
    loc="center left",
    bbox_to_anchor=(1.01, 0.5)
)

fig.subplots_adjust(
    right=0.79
)

save(
    fig,
    "09_candidate_water_cut"
)


# =====================================================================
# FIGURE 10 — FIELD-AVERAGE PRESSURE
#
# FPR is field-average reservoir pressure.
# 300 bar is the imposed candidate WELL BHP,
# not local reservoir pressure.
# =====================================================================

fig, ax = plt.subplots(
    figsize=(9.0, 5.8)
)

for case in ["BASE", "A", "B", "C"]:

    rows = by_case[case]

    dates = [
        dt(r["date"])
        for r in rows
    ]

    pressure = [
        num(r["FPR"])
        for r in rows
    ]

    ax.plot(
        dates,
        pressure,
        marker="o",
        linewidth=2.0,
        markersize=4,
        color=COLORS[case],
        label=LABELS[case]
    )


ax.axhline(
    300.0,
    linestyle="--",
    linewidth=1.4,
    color="black",
    label="Candidate producer BHP = 300 bar"
)

ax.set_title(
    "Standalone Infill Screening — Field-Average Pressure Response"
)

ax.set_xlabel(
    "Forecast date"
)

ax.set_ylabel(
    "Field-average reservoir pressure, FPR (bar(a))"
)

ax.grid(
    True,
    alpha=0.25
)

format_date_axis(ax)

ax.legend(
    loc="center left",
    bbox_to_anchor=(1.01, 0.5)
)

fig.subplots_adjust(
    right=0.75
)

save(
    fig,
    "10_field_pressure_response"
)


# =====================================================================
# FIGURE 11 — TECHNICAL RANKING
# =====================================================================

ranked_cases = sorted(
    ["A", "B", "C"],
    key=lambda c: num(
        cmp[c]["field_forecast_oil"]
    ),
    reverse=True
)

labels = [
    LABELS[c]
    for c in ranked_cases
]

oil = [
    num(
        cmp[c]["field_forecast_oil"]
    ) / 1000.0
    for c in ranked_cases
]

water_oil = [
    (
        num(cmp[c]["field_forecast_water"])
        /
        num(cmp[c]["field_forecast_oil"])
    )
    for c in ranked_cases
]

bar_colors = [
    COLORS[c]
    for c in ranked_cases
]


fig, ax = plt.subplots(
    figsize=(8.5, 5.7)
)

bars = ax.bar(
    labels,
    oil,
    color=bar_colors,
    width=0.68
)

ax.set_title(
    "Standalone Infill Screening — Technical Candidate Ranking"
)

ax.set_ylabel(
    "Five-year forecast oil (10³ Sm³)"
)

ax.grid(
    True,
    axis="y",
    alpha=0.25
)

ax.set_ylim(
    0,
    max(oil) * 1.18
)


for bar, oil_value, ratio in zip(
    bars,
    oil,
    water_oil
):

    ax.text(
        bar.get_x() + bar.get_width() / 2.0,
        bar.get_height() + 0.7,
        (
            f"{oil_value:.1f} kSm³\n"
            f"Water/Oil = {ratio:.2f}"
        ),
        ha="center",
        va="bottom",
        fontsize=10
    )


save(
    fig,
    "11_candidate_ranking"
)


# =====================================================================
# FINAL CAPTIONS
# =====================================================================

captions = DOCS / "final_figure_captions.md"

with captions.open("w") as f:

    f.write(
        "# Project 04 — Final Figure Captions\n\n"
    )

    f.write(
        "## Figure 07 — Five-Year Cumulative Oil\n\n"
        "Five-year standalone forecast cumulative oil for the BASE "
        "case and Candidates A, B and C. All candidate wells were "
        "evaluated independently from the same late-2016 reservoir "
        "state using a common 300 bar BHP producer control. Candidate "
        "A provides the highest forecast oil recovery, followed by "
        "Candidate C, while Candidate B produces very little oil.\n\n"
    )

    f.write(
        "## Figure 08 — Candidate Oil-Rate Response\n\n"
        "Forecast oil-rate response of the three candidate producers. "
        "Candidate A exhibits the highest initial productivity, "
        "Candidate C provides a lower but more persistent response, "
        "and Candidate B remains a very weak oil producer throughout "
        "the forecast.\n\n"
    )

    f.write(
        "## Figure 09 — Candidate Water-Cut Evolution\n\n"
        "Water-cut evolution during active candidate production. "
        "Candidate B remains approximately 99% water dominated. "
        "Candidate C develops a high sustained water cut. Candidate A "
        "initially experiences high water production followed by a "
        "sustained decline in water cut. Connection-level diagnostics "
        "were not stored, so a specific layer-scale mechanism is not "
        "assigned to the Candidate A trend.\n\n"
    )

    f.write(
        "## Figure 10 — Field-Average Pressure Response\n\n"
        "Field-average reservoir-pressure response for BASE and the "
        "three standalone candidate forecasts. The dashed 300 bar line "
        "represents the imposed candidate-well BHP control and should "
        "not be interpreted as local reservoir pressure. The BASE "
        "pressure evolution occurs without active forecast production "
        "or well injection and is treated as internal model pressure "
        "redistribution/equilibration.\n\n"
    )

    f.write(
        "## Figure 11 — Technical Candidate Ranking\n\n"
        "Technical ranking based on five-year forecast oil recovery "
        "under common screening assumptions, with cumulative water/oil "
        "ratio shown as an additional production-quality indicator. "
        "Candidate A ranks first, Candidate C second, and Candidate B "
        "is rejected because its production is overwhelmingly water "
        "dominated.\n"
    )

print()
print("WROTE:", captions)

print()
print("=" * 86)
print("FINAL FORECAST FIGURE POLISH COMPLETE")
print("=" * 86)
print()
print("Frozen engineering result:")
print("A > C >> B")
print()
print("No simulation data were changed.")
