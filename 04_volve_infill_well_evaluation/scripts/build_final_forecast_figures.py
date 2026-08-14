from pathlib import Path
from datetime import datetime
import csv
import math
import sys

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    print()
    print("ERROR: matplotlib is not installed in this Python environment.")
    print()
    print("Check first with:")
    print("    python3 -m pip --version")
    print()
    print("If pip is available, install matplotlib with:")
    print("    python3 -m pip install --user matplotlib")
    print()
    sys.exit(1)


# ======================================================================
# PROJECT 04 — FINAL FORECAST FIGURES
# ======================================================================

REPO = Path(
    "/mnt/c/Users/ADMIN/Desktop/GitHub/"
    "Reservoir-Engineering-Portfolio/"
    "04_volve_infill_well_evaluation"
)

RESULTS = REPO / "results"
FIGDIR  = REPO / "figures" / "final"
DOCS    = REPO / "docs"

FIGDIR.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

TS_FILE = RESULTS / "final_forecast_timeseries.csv"
CMP_FILE = RESULTS / "final_forecast_comparison.csv"

CASES = ["BASE", "A", "B", "C"]
CANDIDATES = ["A", "B", "C"]


def fnum(value):
    try:
        x = float(value)
        if math.isfinite(x):
            return x
    except Exception:
        pass
    return float("nan")


def date_value(value):
    return datetime.strptime(value, "%Y-%m-%d")


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def save_figure(fig, stem):
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


if not TS_FILE.exists():
    raise FileNotFoundError(TS_FILE)

if not CMP_FILE.exists():
    raise FileNotFoundError(CMP_FILE)


timeseries = read_csv(TS_FILE)
comparison = read_csv(CMP_FILE)

by_case = {}

for case in CASES:
    rows = [
        r for r in timeseries
        if r["case"] == case
    ]

    rows.sort(
        key=lambda r: r["date"]
    )

    by_case[case] = rows


cmp_by_case = {
    r["case"]: r
    for r in comparison
}


# ======================================================================
# FIGURE 01 — CUMULATIVE FORECAST OIL
# ======================================================================

fig, ax = plt.subplots(
    figsize=(8.5, 5.5)
)

for case in CASES:

    rows = by_case[case]

    dates = [
        date_value(r["date"])
        for r in rows
    ]

    fopt = [
        fnum(r["FOPT"])
        for r in rows
    ]

    start = fopt[0]

    cumulative = [
        (x - start) / 1000.0
        for x in fopt
    ]

    label = (
        "BASE"
        if case == "BASE"
        else f"Candidate {case}"
    )

    ax.plot(
        dates,
        cumulative,
        marker="o",
        linewidth=1.8,
        markersize=3.5,
        label=label
    )

ax.set_title(
    "Five-Year Standalone Infill Forecast — Cumulative Oil"
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

ax.legend()

fig.autofmt_xdate()

save_figure(
    fig,
    "07_forecast_cumulative_oil"
)


# ======================================================================
# FIGURE 02 — CANDIDATE OIL RATE
# ======================================================================

fig, ax = plt.subplots(
    figsize=(8.5, 5.5)
)

for case in CANDIDATES:

    rows = by_case[case]

    dates = [
        date_value(r["date"])
        for r in rows
    ]

    wopr = [
        fnum(r["WOPR"])
        for r in rows
    ]

    ax.plot(
        dates,
        wopr,
        marker="o",
        linewidth=1.8,
        markersize=3.5,
        label=f"Candidate {case}"
    )

ax.set_title(
    "Candidate Oil-Rate Response"
)

ax.set_xlabel(
    "Forecast date"
)

ax.set_ylabel(
    "Oil production rate (Sm³/day)"
)

ax.grid(
    True,
    alpha=0.25
)

ax.legend()

fig.autofmt_xdate()

save_figure(
    fig,
    "08_candidate_oil_rate"
)


# ======================================================================
# FIGURE 03 — CANDIDATE WATER CUT
# ======================================================================

fig, ax = plt.subplots(
    figsize=(8.5, 5.5)
)

for case in CANDIDATES:

    rows = by_case[case]

    dates = [
        date_value(r["date"])
        for r in rows
    ]

    wwct = [
        100.0 * fnum(r["WWCT"])
        for r in rows
    ]

    ax.plot(
        dates,
        wwct,
        marker="o",
        linewidth=1.8,
        markersize=3.5,
        label=f"Candidate {case}"
    )

ax.set_title(
    "Candidate Water-Cut Evolution"
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

ax.legend()

fig.autofmt_xdate()

save_figure(
    fig,
    "09_candidate_water_cut"
)


# ======================================================================
# FIGURE 04 — FIELD-AVERAGE PRESSURE RESPONSE
# ======================================================================

fig, ax = plt.subplots(
    figsize=(8.5, 5.5)
)

for case in CASES:

    rows = by_case[case]

    dates = [
        date_value(r["date"])
        for r in rows
    ]

    fpr = [
        fnum(r["FPR"])
        for r in rows
    ]

    label = (
        "BASE"
        if case == "BASE"
        else f"Candidate {case}"
    )

    ax.plot(
        dates,
        fpr,
        marker="o",
        linewidth=1.8,
        markersize=3.5,
        label=label
    )

ax.axhline(
    300.0,
    linestyle="--",
    linewidth=1.2,
    label="Candidate BHP control = 300 bar"
)

ax.set_title(
    "Field-Average Pressure Response"
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

ax.legend()

fig.autofmt_xdate()

save_figure(
    fig,
    "10_field_pressure_response"
)


# ======================================================================
# ENGINEERING SUMMARY
# ======================================================================

summary_rows = []

for case in CANDIDATES:

    cmp = cmp_by_case[case]
    ts = by_case[case]

    active = [
        r for r in ts
        if (
            abs(fnum(r["WOPR"]))
            +
            abs(fnum(r["WWPR"]))
        ) > 1.0e-8
    ]

    wc = [
        fnum(r["WWCT"])
        for r in active
        if math.isfinite(
            fnum(r["WWCT"])
        )
    ]

    first_wc = (
        100.0 * fnum(active[0]["WWCT"])
        if active else float("nan")
    )

    final_wc = (
        100.0 * fnum(active[-1]["WWCT"])
        if active else float("nan")
    )

    max_wc = (
        100.0 * max(wc)
        if wc else float("nan")
    )

    oil = fnum(
        cmp["field_forecast_oil"]
    )

    water = fnum(
        cmp["field_forecast_water"]
    )

    ratio = (
        water / oil
        if oil > 0
        else float("nan")
    )

    if case == "A":
        recommendation = (
            "Preferred technical candidate; "
            "carry forward for further evaluation"
        )

    elif case == "C":
        recommendation = (
            "Secondary technical opportunity"
        )

    else:
        recommendation = (
            "Reject under current screening assumptions; "
            "strongly water dominated"
        )

    summary_rows.append({
        "candidate": case,
        "forecast_oil_sm3": oil,
        "forecast_water_sm3": water,
        "water_oil_ratio": ratio,
        "peak_wopr_sm3_day":
            fnum(cmp["candidate_peak_WOPR"]),
        "final_wopr_sm3_day":
            fnum(cmp["candidate_end_WOPR"]),
        "first_active_water_cut_pct":
            first_wc,
        "maximum_water_cut_pct":
            max_wc,
        "final_water_cut_pct":
            final_wc,
        "final_fpr_bara":
            fnum(cmp["FPR_end"]),
        "bhp_control_bara":
            fnum(cmp["candidate_mean_active_WBHP"]),
        "recommendation":
            recommendation,
    })


summary_csv = (
    RESULTS /
    "final_engineering_summary.csv"
)

with summary_csv.open(
    "w",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=list(
            summary_rows[0].keys()
        )
    )

    writer.writeheader()
    writer.writerows(
        summary_rows
    )

print("WROTE:", summary_csv)


# ======================================================================
# FIGURE 05 — CANDIDATE RANKING
# ======================================================================

ranked = sorted(
    summary_rows,
    key=lambda r: r["forecast_oil_sm3"],
    reverse=True
)

labels = [
    f"Candidate {r['candidate']}"
    for r in ranked
]

oil_k = [
    r["forecast_oil_sm3"] / 1000.0
    for r in ranked
]

fig, ax = plt.subplots(
    figsize=(8.0, 5.5)
)

bars = ax.bar(
    labels,
    oil_k
)

ax.set_title(
    "Technical Candidate Ranking by Forecast Oil"
)

ax.set_ylabel(
    "Five-year forecast oil (10³ Sm³)"
)

ax.grid(
    True,
    axis="y",
    alpha=0.25
)

for bar, row in zip(
    bars,
    ranked
):
    height = bar.get_height()

    ratio = row[
        "water_oil_ratio"
    ]

    ax.text(
        bar.get_x()
        + bar.get_width() / 2.0,
        height,
        (
            f"{height:.1f}\n"
            f"W/O={ratio:.2f}"
        ),
        ha="center",
        va="bottom",
        fontsize=9
    )

save_figure(
    fig,
    "11_candidate_ranking"
)


# ======================================================================
# FINAL MARKDOWN SUMMARY
# ======================================================================

md = (
    DOCS /
    "final_forecast_results.md"
)

with md.open("w") as f:

    f.write(
        "# Project 04 — Final Forecast Results\n\n"
    )

    f.write(
        "## Forecast design\n\n"
    )

    f.write(
        "- Forecast period: 1 October 2016 to 1 October 2021.\n"
        "- Historical wells remain inactive during the forecast.\n"
        "- No active water or gas injection occurs during the forecast.\n"
        "- Each candidate is evaluated independently under a common "
        "300 bar BHP producer control.\n"
        "- BASE contains no active forecast wells.\n\n"
    )

    f.write(
        "## Candidate comparison\n\n"
    )

    f.write(
        "| Rank | Candidate | Oil (10³ Sm³) | "
        "Water (10³ Sm³) | Water/Oil | "
        "Peak WOPR (Sm³/d) | Final WOPR (Sm³/d) | "
        "Recommendation |\n"
    )

    f.write(
        "|---:|---|---:|---:|---:|---:|---:|---|\n"
    )

    for rank, row in enumerate(
        ranked,
        start=1
    ):

        f.write(
            f"| {rank} "
            f"| {row['candidate']} "
            f"| {row['forecast_oil_sm3']/1000:.2f} "
            f"| {row['forecast_water_sm3']/1000:.2f} "
            f"| {row['water_oil_ratio']:.2f} "
            f"| {row['peak_wopr_sm3_day']:.2f} "
            f"| {row['final_wopr_sm3_day']:.2f} "
            f"| {row['recommendation']} |\n"
        )

    f.write(
        "\n## Engineering interpretation\n\n"
    )

    f.write(
        "**Candidate A** is the preferred technical screening target. "
        "It gives the largest five-year oil recovery and the highest "
        "initial oil productivity among the tested locations.\n\n"
    )

    f.write(
        "**Candidate C** remains a secondary opportunity. Its high "
        "remaining oil saturation produces meaningful oil, but the "
        "five-year recovery is lower than Candidate A and water cut "
        "remains high for much of the forecast.\n\n"
    )

    f.write(
        "**Candidate B** is rejected under the tested assumptions. "
        "Its response is overwhelmingly water dominated and provides "
        "very little oil recovery.\n\n"
    )

    f.write(
        "The experiment is a deterministic late-life standalone "
        "technical screening study. It does not represent a full "
        "active-field development optimization or a commercial "
        "drill/no-drill sanction decision.\n\n"
    )

    f.write(
        "High remaining oil saturation alone is not sufficient to "
        "identify the strongest infill target. Pore volume, "
        "permeability, pressure, sweep history, phase mobility, "
        "connectivity and completion design must be considered "
        "together.\n"
    )

print("WROTE:", md)


# ======================================================================
# CONSOLE SUMMARY
# ======================================================================

print()
print("=" * 90)
print("PROJECT 04 — FINAL ENGINEERING SUMMARY")
print("=" * 90)

print(
    f"{'RANK':<7}"
    f"{'CASE':<10}"
    f"{'OIL kSm3':>12}"
    f"{'WATER kSm3':>14}"
    f"{'W/O':>10}"
    f"{'PEAK WOPR':>14}"
    f"{'FINAL WOPR':>14}"
)

print("-" * 90)

for rank, row in enumerate(
    ranked,
    start=1
):

    print(
        f"{rank:<7}"
        f"{row['candidate']:<10}"
        f"{row['forecast_oil_sm3']/1000:>12.2f}"
        f"{row['forecast_water_sm3']/1000:>14.2f}"
        f"{row['water_oil_ratio']:>10.2f}"
        f"{row['peak_wopr_sm3_day']:>14.2f}"
        f"{row['final_wopr_sm3_day']:>14.2f}"
    )

print()
print(
    "Technical screening conclusion: "
    "A > C >> B"
)

print()
print(
    "Candidate A: preferred for further technical evaluation."
)

print(
    "Candidate C: secondary opportunity."
)

print(
    "Candidate B: reject under current screening assumptions."
)

print()
print("=" * 90)
print("FINAL FIGURE BUILD COMPLETE")
print("=" * 90)
