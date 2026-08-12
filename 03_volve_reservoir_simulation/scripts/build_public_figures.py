from pathlib import Path
import csv
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FINAL = ROOT / "figures"

FINAL.mkdir(parents=True, exist_ok=True)

# ============================================================
# Helpers
# ============================================================

def read_csv_float(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def values(rows, key):
    return np.array([float(r[key]) for r in rows], dtype=float)


def finish(fig, path):
    fig.savefig(
        path,
        dpi=300,
        bbox_inches="tight",
        facecolor="white"
    )
    plt.close(fig)
    print("CREATED:", path)


# ============================================================
# Load compact field comparison
# ============================================================

field_rows = read_csv_float(
    RESULTS / "opm_vs_eclipse_field_comparison.csv"
)

t = values(field_rows, "TIME")


# ============================================================
# FIGURE 01 — Field rates
# ============================================================

rate_specs = [
    (
        "FOPR",
        "Field Oil Production Rate",
        "Oil rate [Sm³/d]"
    ),
    (
        "FWPR",
        "Field Water Production Rate",
        "Water rate [Sm³/d]"
    ),
    (
        "FGPR",
        "Field Gas Production Rate",
        "Gas rate [Sm³/d]"
    ),
    (
        "FWIR",
        "Field Water Injection Rate",
        "Water injection rate [Sm³/d]"
    ),
]

fig, axes = plt.subplots(
    2, 2,
    figsize=(13.5, 8.5),
    sharex=True
)

for ax, (vec, title, ylabel) in zip(
    axes.flat,
    rate_specs
):
    eclipse = values(
        field_rows,
        f"{vec}_ECLIPSE"
    )

    opm = values(
        field_rows,
        f"{vec}_OPM"
    )

    ax.plot(
        t,
        eclipse,
        "k--",
        linewidth=1.7,
        label="Released ECLIPSE"
    )

    ax.plot(
        t,
        opm,
        linewidth=1.5,
        label="OPM Flow"
    )

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)

for ax in axes[1, :]:
    ax.set_xlabel("Simulation time [days]")

handles, labels = axes[0, 0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="upper center",
    ncol=2,
    frameon=False,
    bbox_to_anchor=(0.5, 0.935)
)

fig.suptitle(
    "Volve Field Performance: Released ECLIPSE vs OPM Flow",
    fontsize=17,
    fontweight="bold",
    y=0.985
)

fig.tight_layout(rect=[0, 0, 1, 0.89])

finish(
    fig,
    FINAL / "01_volve_opm_vs_eclipse_field_rates.png"
)


# ============================================================
# FIGURE 02 — cumulative production and pressure
# ============================================================

fig, axes = plt.subplots(
    2, 2,
    figsize=(13.5, 8.5),
    sharex=True
)

cum_specs = [
    (
        "FOPT",
        "Cumulative Oil Production",
        1e6,
        "Cumulative oil [10⁶ Sm³]"
    ),
    (
        "FWPT",
        "Cumulative Water Production",
        1e6,
        "Cumulative water [10⁶ Sm³]"
    ),
    (
        "FGPT",
        "Cumulative Gas Production",
        1e9,
        "Cumulative gas [10⁹ Sm³]"
    ),
]

for ax, (vec, title, scale, ylabel) in zip(
    [axes[0, 0], axes[0, 1], axes[1, 0]],
    cum_specs
):
    eclipse = values(
        field_rows,
        f"{vec}_ECLIPSE"
    ) / scale

    opm = values(
        field_rows,
        f"{vec}_OPM"
    ) / scale

    ax.plot(
        t,
        eclipse,
        "k--",
        linewidth=1.7
    )

    ax.plot(
        t,
        opm,
        linewidth=1.5
    )

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)

ax = axes[1, 1]

ax.plot(
    t,
    values(field_rows, "FPR_ECLIPSE"),
    "k--",
    linewidth=1.7
)

ax.plot(
    t,
    values(field_rows, "FPR_OPM"),
    linewidth=1.5
)

ax.set_title("Field Pressure")
ax.set_ylabel("Field pressure [bar]")
ax.grid(alpha=0.25)

for ax in axes[1, :]:
    ax.set_xlabel("Simulation time [days]")

handles = [
    plt.Line2D(
        [0], [0],
        linestyle="--",
        linewidth=1.7,
        marker=None
    ),
    plt.Line2D(
        [0], [0],
        linewidth=1.7,
        marker=None
    )
]

fig.legend(
    handles,
    ["Released ECLIPSE", "OPM Flow"],
    loc="upper center",
    ncol=2,
    frameon=False,
    bbox_to_anchor=(0.5, 0.935)
)

fig.suptitle(
    "Volve Cumulative Production and Pressure: ECLIPSE vs OPM Flow",
    fontsize=17,
    fontweight="bold",
    y=0.985
)

fig.tight_layout(rect=[0, 0, 1, 0.89])

finish(
    fig,
    FINAL / "02_volve_opm_vs_eclipse_cumulative_pressure.png"
)


# ============================================================
# Load compact key-well comparison
# ============================================================

well_rows = read_csv_float(
    RESULTS / "opm_vs_eclipse_key_well_comparison.csv"
)

tw = values(well_rows, "TIME")

wells = [
    "P-F-14",
    "P-F-12",
    "P-F-11B",
    "P-F-15D",
]

ecl_well = {"TIME": tw}
opm_well = {"TIME": tw}

for variable in ["WOPR", "WBHP", "WWCT"]:
    for well in wells:
        ecl_well[f"{variable}:{well}"] = values(
            well_rows,
            f"{variable}_{well}_ECLIPSE"
        )

        opm_well[f"{variable}:{well}"] = values(
            well_rows,
            f"{variable}_{well}_OPM"
        )


# ============================================================
# FIGURE 03 — Key producer oil rates
# ============================================================

fig, axes = plt.subplots(
    2, 2,
    figsize=(13, 8.2),
    sharex=True
)

for ax, well in zip(
    axes.flat,
    wells
):
    ax.plot(
        tw,
        ecl_well[f"WOPR:{well}"],
        "k--",
        linewidth=1.7
    )

    ax.plot(
        tw,
        opm_well[f"WOPR:{well}"],
        linewidth=1.5
    )

    ax.set_title(
        well,
        fontweight="bold"
    )

    ax.set_ylabel(
        "Oil production rate [Sm³/d]"
    )

    ax.grid(alpha=0.25)

for ax in axes[1, :]:
    ax.set_xlabel(
        "Simulation time [days]"
    )

fig.legend(
    handles,
    ["Released ECLIPSE", "OPM Flow"],
    loc="upper center",
    ncol=2,
    frameon=False,
    bbox_to_anchor=(0.5, 0.935)
)

fig.suptitle(
    "Volve Key Producer Oil Rates: Released ECLIPSE vs OPM Flow",
    fontsize=17,
    fontweight="bold",
    y=0.985
)

fig.tight_layout(rect=[0, 0, 1, 0.89])

finish(
    fig,
    FINAL / "03_volve_key_well_oil_rate_comparison.png"
)


# ============================================================
# FIGURE 04 — Key-well BHP and water cut
# ============================================================

fig, axes = plt.subplots(
    2, 4,
    figsize=(15.5, 7.2),
    sharex=True
)

for j, well in enumerate(wells):

    ax = axes[0, j]

    ax.plot(
        tw,
        ecl_well[f"WBHP:{well}"],
        "k--",
        linewidth=1.6
    )

    ax.plot(
        tw,
        opm_well[f"WBHP:{well}"],
        linewidth=1.4
    )

    ax.set_title(
        well,
        fontweight="bold"
    )

    if j == 0:
        ax.set_ylabel("BHP [bar]")

    ax.grid(alpha=0.25)

    ax = axes[1, j]

    ax.plot(
        tw,
        ecl_well[f"WWCT:{well}"],
        "k--",
        linewidth=1.6
    )

    ax.plot(
        tw,
        opm_well[f"WWCT:{well}"],
        linewidth=1.4
    )

    if j == 0:
        ax.set_ylabel("Water cut [-]")

    ax.set_xlabel(
        "Simulation time [days]"
    )

    ax.grid(alpha=0.25)

fig.legend(
    handles,
    ["Released ECLIPSE", "OPM Flow"],
    loc="upper center",
    ncol=2,
    frameon=False,
    bbox_to_anchor=(0.5, 0.935)
)

fig.suptitle(
    "Volve Key-Well Pressure and Water-Cut Response: ECLIPSE vs OPM Flow",
    fontsize=17,
    fontweight="bold",
    y=0.985
)

fig.tight_layout(rect=[0, 0, 1, 0.89])

finish(
    fig,
    FINAL / "04_volve_key_well_bhp_watercut_comparison.png"
)


# ============================================================
# FIGURE 05 — Quantitative error summary
# ============================================================

field_metrics = read_csv_float(
    RESULTS / "opm_vs_eclipse_field_metrics.csv"
)

well_oil_metrics = read_csv_float(
    RESULTS / "opm_vs_eclipse_well_oil_metrics.csv"
)

bhp_wc_metrics = read_csv_float(
    RESULTS / "opm_vs_eclipse_bhp_watercut_metrics.csv"
)

field_order = [
    "FOPR",
    "FWPR",
    "FGPR",
    "FOPT",
    "FWPT",
    "FGPT",
    "FPR",
]

field_map = {
    r["VECTOR"]: float(r["NRMSE_PERCENT"])
    for r in field_metrics
}

well_oil_map = {
    r["WELL"]: float(r["NRMSE_PERCENT"])
    for r in well_oil_metrics
}

bhp_map = {
    r["WELL"]: float(r["NRMSE_PERCENT"])
    for r in bhp_wc_metrics
    if r["VARIABLE"] == "WBHP"
}

wc_map = {
    r["WELL"]: float(r["NRMSE_PERCENT"])
    for r in bhp_wc_metrics
    if r["VARIABLE"] == "WWCT"
}

fig, axes = plt.subplots(
    1, 3,
    figsize=(15.5, 5.1)
)

# Panel A
ax = axes[0]

vals = [
    field_map[v]
    for v in field_order
]

bars = ax.bar(
    field_order,
    vals
)

ax.set_title(
    "Field-scale response",
    fontweight="bold"
)

ax.set_ylabel("NRMSE [%]")
ax.set_ylim(0, max(vals) * 1.18)
ax.grid(axis="y", alpha=0.25)

for bar, val in zip(bars, vals):
    ax.text(
        bar.get_x() + bar.get_width()/2,
        val + max(vals)*0.025,
        f"{val:.2f}",
        ha="center",
        va="bottom",
        fontsize=9
    )

# Explicitly disable scientific offset text
ax.ticklabel_format(
    axis="y",
    style="plain",
    useOffset=False
)

# Panel B
ax = axes[1]

vals = [
    well_oil_map[w]
    for w in wells
]

bars = ax.bar(
    wells,
    vals
)

ax.set_title(
    "Producer oil-rate response",
    fontweight="bold"
)

ax.set_ylabel("NRMSE [%]")
ax.set_ylim(0, max(vals) * 1.18)
ax.grid(axis="y", alpha=0.25)

for bar, val in zip(bars, vals):
    ax.text(
        bar.get_x() + bar.get_width()/2,
        val + max(vals)*0.025,
        f"{val:.2f}",
        ha="center",
        fontsize=9
    )

# Panel C
ax = axes[2]

x = np.arange(len(wells))
width = 0.36

bhp_vals = [
    bhp_map[w]
    for w in wells
]

wc_vals = [
    wc_map[w]
    for w in wells
]

b1 = ax.bar(
    x - width/2,
    bhp_vals,
    width,
    label="BHP"
)

b2 = ax.bar(
    x + width/2,
    wc_vals,
    width,
    label="Water cut"
)

ax.set_xticks(x)
ax.set_xticklabels(wells)

ax.set_title(
    "Producer pressure and water cut",
    fontweight="bold"
)

ax.set_ylabel("NRMSE [%]")
ax.set_ylim(
    0,
    max(wc_vals) * 1.18
)

ax.grid(axis="y", alpha=0.25)
ax.legend(frameon=False)

for bars, vals in [
    (b1, bhp_vals),
    (b2, wc_vals)
]:
    for bar, val in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            val + max(wc_vals)*0.018,
            f"{val:.2f}",
            ha="center",
            fontsize=8
        )

fig.suptitle(
    "Volve Cross-Simulator Reproduction Error Summary",
    fontsize=17,
    fontweight="bold",
    y=0.99
)

fig.tight_layout(rect=[0, 0, 1, 0.92])

finish(
    fig,
    FINAL / "05_volve_opm_vs_eclipse_error_summary.png"
)


# ============================================================
# FIGURE 06 — FOPT sensitivity screening
# ============================================================

effects_rows = read_csv_float(
    RESULTS / "sensitivity_effects_vs_base.csv"
)

fopt_effect = {
    r["CASE"]: float(r["DELTA_PERCENT"])
    for r in effects_rows
    if r["METRIC"] == "FOPT"
}

families = [
    (
        "North-side pore volume",
        fopt_effect["sens_northpv_low"],
        fopt_effect["sens_northpv_high"],
    ),
    (
        "P-F-12 local permeability",
        fopt_effect["sens_f12perm_low"],
        fopt_effect["sens_f12perm_high"],
    ),
    (
        "Fault connectivity",
        fopt_effect["sens_fault_low"],
        fopt_effect["sens_fault_high"],
    ),
]

fig, ax = plt.subplots(
    figsize=(10, 5.2)
)

low_color = "tab:blue"
high_color = "tab:orange"

for i, (name, low, high) in enumerate(families):

    ax.hlines(
        i,
        low,
        high,
        linewidth=2,
        color="0.45"
    )

    ax.scatter(
        low,
        i,
        marker="o",
        s=95,
        color=low_color,
        zorder=3,
        label="Low case" if i == 0 else None
    )

    ax.scatter(
        high,
        i,
        marker="s",
        s=90,
        color=high_color,
        zorder=3,
        label="High case" if i == 0 else None
    )

    # Larger separation for small fault values
    low_yoff = -25 if i == 2 else -20
    high_yoff = 14

    ax.annotate(
        f"{low:+.3f}%",
        (low, i),
        xytext=(0, low_yoff),
        textcoords="offset points",
        ha="center",
        fontsize=10
    )

    ax.annotate(
        f"{high:+.3f}%",
        (high, i),
        xytext=(0, high_yoff),
        textcoords="offset points",
        ha="center",
        fontsize=10
    )

ax.axvline(
    0,
    linewidth=1.2,
    color="0.25"
)

ax.set_yticks(
    range(len(families))
)

ax.set_yticklabels(
    [x[0] for x in families]
)

ax.invert_yaxis()

ax.set_xlim(-0.75, 0.72)

ax.set_xlabel(
    "Change in final cumulative oil relative to Base, ΔFOPT [%]"
)

ax.set_title(
    "Volve Reservoir Sensitivity Screening — Final Cumulative Oil",
    fontweight="bold"
)

ax.grid(
    axis="x",
    alpha=0.25
)

ax.legend(
    frameon=False,
    loc="lower left"
)

fig.tight_layout()

finish(
    fig,
    FINAL / "06_volve_sensitivity_final_fopt.png"
)


# ============================================================
# FIGURE 07 — North PV ΔFOPT through time
# ============================================================

sens_rows = read_csv_float(
    RESULTS / "sensitivity_timeseries_all_cases.csv"
)

case_data = {}

for row in sens_rows:
    case = row["CASE"]

    if case not in {
        "BASE",
        "sens_northpv_low",
        "sens_northpv_high"
    }:
        continue

    case_data.setdefault(
        case,
        []
    ).append(
        (
            float(row["TIME"]),
            float(row["FOPT"])
        )
    )

base_map = {
    t_: value
    for t_, value
    in case_data["BASE"]
}

fig, ax = plt.subplots(
    figsize=(9.5, 5.2)
)

for case, label, color in [
    (
        "sens_northpv_low",
        "North PV Low",
        low_color
    ),
    (
        "sens_northpv_high",
        "North PV High",
        high_color
    ),
]:

    times = []
    delta = []

    for time, fopt in case_data[case]:

        base = base_map[time]

        if base <= 0:
            continue

        times.append(time)

        delta.append(
            100.0 *
            (fopt - base) /
            base
        )

    ax.plot(
        times,
        delta,
        linewidth=2.0,
        label=label,
        color=color
    )

    ax.annotate(
        f"{delta[-1]:+.3f}%",
        (times[-1], delta[-1]),
        xytext=(-55, 8 if delta[-1] > 0 else -13),
        textcoords="offset points",
        fontsize=10
    )

ax.axhline(
    0,
    linewidth=1.1,
    color="0.25"
)

ax.set_xlabel(
    "Simulation time [days]"
)

ax.set_ylabel(
    "Change in cumulative oil relative to Base, ΔFOPT [%]"
)

ax.set_title(
    "North-side Pore Volume Sensitivity Through Time",
    fontweight="bold"
)

ax.grid(alpha=0.25)

ax.legend(
    frameon=False,
    loc="upper left"
)

fig.tight_layout()

finish(
    fig,
    FINAL / "07_volve_northpv_fopt_change_vs_base.png"
)


# ============================================================
# Final inventory
# ============================================================

print("\n===================================================")
print(" FINAL PUBLIC FIGURE SET")
print("===================================================")

for p in sorted(FINAL.glob("*.png")):
    print(p.name, f"{p.stat().st_size/1024:.1f} KB")

print("\nALL PUBLIC FIGURES CREATED")
