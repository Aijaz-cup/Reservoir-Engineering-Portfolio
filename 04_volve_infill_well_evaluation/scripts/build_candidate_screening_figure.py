from pathlib import Path
import csv
import math
import matplotlib.pyplot as plt

REPO = Path(
    "/mnt/c/Users/ADMIN/Desktop/GitHub/"
    "Reservoir-Engineering-Portfolio/"
    "04_volve_infill_well_evaluation"
)

RESULTS = REPO / "results"
FIGDIR = REPO / "figures" / "final"

FIGDIR.mkdir(
    parents=True,
    exist_ok=True
)

completion_file = (
    RESULTS /
    "final_candidate_completion_windows.csv"
)

screening_file = (
    RESULTS /
    "candidate_screening_summary.csv"
)


# ------------------------------------------------------------------
# Load final completion metrics
# ------------------------------------------------------------------

with completion_file.open(newline="") as f:
    completion_rows = list(
        csv.DictReader(f)
    )


# ------------------------------------------------------------------
# Load spacing information from full-column screening
# ------------------------------------------------------------------

with screening_file.open(newline="") as f:
    screening_rows = list(
        csv.DictReader(f)
    )


source_to_final = {
    "ALT_70_21": "A",
    "ALT_66_32": "B",
    "ALT_46_27": "C",
}

spacing = {}

for r in screening_rows:
    src = r["candidate"]

    if src in source_to_final:
        spacing[
            source_to_final[src]
        ] = float(
            r[
                "nearest_completion_distance_IJ_cells"
            ]
        )


data = {}

for r in completion_rows:

    case = r["candidate"].split("_")[-1]

    data[case] = {
        "oilpv":
            float(r["interval_oil_pv_proxy"]),

        "soil":
            float(r["weighted_SOIL"]),

        "dswat":
            float(r["weighted_delta_SWAT"]),

        "perm":
            float(r["median_PERMX"]),

        "pressure":
            float(r["weighted_pressure"]),

        "K1":
            int(r["K1"]),

        "K2":
            int(r["K2"]),

        "spacing":
            spacing[case],
    }


cases = ["A", "B", "C"]

colors = {
    "A": "#1f77b4",
    "B": "#ff7f0e",
    "C": "#2ca02c",
}

labels = [
    (
        f"Candidate {c}\n"
        f"K{data[c]['K1']}–{data[c]['K2']}\n"
        f"spacing={data[c]['spacing']:.2f} cells"
    )
    for c in cases
]


fig, axes = plt.subplots(
    2,
    2,
    figsize=(11.5, 8.0)
)

fig.suptitle(
    "Final Candidate Screening Before Forecasting",
    fontsize=17,
    y=0.98
)


# ==================================================================
# Panel A — oil-filled pore-volume screening metric
# ==================================================================

ax = axes[0, 0]

vals = [
    data[c]["oilpv"]
    for c in cases
]

bars = ax.bar(
    labels,
    vals,
    color=[colors[c] for c in cases]
)

ax.set_title(
    "Completion Oil-Filled Pore-Volume Screening Metric"
)

ax.set_ylabel(
    "Oil-Filled PV Screening Metric (model units)"
)

ax.grid(
    True,
    axis="y",
    alpha=0.25
)

for bar, val in zip(bars, vals):
    ax.text(
        bar.get_x() + bar.get_width()/2,
        bar.get_height(),
        f"{val:,.0f}",
        ha="center",
        va="bottom",
        fontsize=9
    )


# ==================================================================
# Panel B — remaining oil saturation
# ==================================================================

ax = axes[0, 1]

vals = [
    100.0 * data[c]["soil"]
    for c in cases
]

bars = ax.bar(
    labels,
    vals,
    color=[colors[c] for c in cases]
)

ax.set_title(
    "Oil-PV-Weighted Remaining Oil Saturation"
)

ax.set_ylabel(
    "Weighted oil saturation (%)"
)

ax.set_ylim(
    0,
    100
)

ax.grid(
    True,
    axis="y",
    alpha=0.25
)

for bar, val in zip(bars, vals):
    ax.text(
        bar.get_x() + bar.get_width()/2,
        bar.get_height(),
        f"{val:.1f}%",
        ha="center",
        va="bottom",
        fontsize=9
    )


# ==================================================================
# Panel C — historical water sweep
# ==================================================================

ax = axes[1, 0]

vals = [
    100.0 * data[c]["dswat"]
    for c in cases
]

bars = ax.bar(
    labels,
    vals,
    color=[colors[c] for c in cases]
)

ax.axhline(
    0,
    linewidth=0.8,
    color="black"
)

ax.set_title(
    "Historical Water-Saturation Change"
)

ax.set_ylabel(
    "Oil-PV-weighted ΔSw (percentage points)"
)

ax.grid(
    True,
    axis="y",
    alpha=0.25
)

for bar, val in zip(bars, vals):

    va = (
        "bottom"
        if val >= 0
        else "top"
    )

    ax.text(
        bar.get_x() + bar.get_width()/2,
        bar.get_height(),
        f"{val:.1f}",
        ha="center",
        va=va,
        fontsize=9
    )


# ==================================================================
# Panel D — permeability
# ==================================================================

ax = axes[1, 1]

vals = [
    data[c]["perm"]
    for c in cases
]

bars = ax.bar(
    labels,
    vals,
    color=[colors[c] for c in cases]
)

ax.set_title(
    "Completion Permeability"
)

ax.set_ylabel(
    "Median PERMX (mD)"
)

ax.grid(
    True,
    axis="y",
    alpha=0.25
)

for bar, val in zip(bars, vals):
    ax.text(
        bar.get_x() + bar.get_width()/2,
        bar.get_height(),
        f"{val:,.0f}",
        ha="center",
        va="bottom",
        fontsize=9
    )


# ------------------------------------------------------------------
# Figure note
# ------------------------------------------------------------------

fig.text(
    0.5,
    0.015,
    (
        "Screening metrics describe the final completion intervals "
        "tested in the OPM forecasts. Positive ΔSw indicates greater "
        "historical water invasion. Candidate spacing is reported in "
        "grid-index cells and is not a physical metric distance."
    ),
    ha="center",
    va="bottom",
    fontsize=9
)

fig.tight_layout(
    rect=[0, 0.055, 1, 0.95]
)


png = (
    FIGDIR /
    "06_final_candidate_screening.png"
)

pdf = (
    FIGDIR /
    "06_final_candidate_screening.pdf"
)

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

print()
print("WROTE:")
print(png)
print(pdf)

print()
print("=" * 90)
print("FIGURE 06 — SCREENING INTERPRETATION")
print("=" * 90)

print(
    "Candidate A:"
    " high oil-filled volume + very strong permeability,"
    " with comparatively limited completion-scale sweep."
)

print(
    "Candidate B:"
    " lower remaining oil saturation + strong historical water sweep."
)

print(
    "Candidate C:"
    " very high remaining oil saturation and essentially no sweep,"
    " but a much smaller oil-filled pore-volume opportunity."
)

print()
print(
    "This provides the pre-forecast engineering hypothesis"
    " tested by Figures 07–11."
)
