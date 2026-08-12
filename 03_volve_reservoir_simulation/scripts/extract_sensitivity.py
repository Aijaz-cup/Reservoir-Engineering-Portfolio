from pathlib import Path
import subprocess
import csv
import math
import argparse

parser = argparse.ArgumentParser(
    description="Extract compact sensitivity results from completed OPM Flow runs."
)
parser.add_argument(
    "simulation_root",
    type=Path,
    help="Path to the full Project_03_Reservoir_Simulation working directory."
)
parser.add_argument(
    "--output-dir",
    type=Path,
    default=None,
    help="Optional output directory. Default: <simulation_root>/analysis"
)

args = parser.parse_args()
ROOT = args.simulation_root.resolve()

cases = {
    "BASE": ROOT / "work/opm_compat_full/VOLVE_2016.SMSPEC",
    "sens_fault_low": ROOT / "work/sensitivity_outputs/sens_fault_low/VOLVE_2016.SMSPEC",
    "sens_fault_high": ROOT / "work/sensitivity_outputs/sens_fault_high/VOLVE_2016.SMSPEC",
    "sens_f12perm_low": ROOT / "work/sensitivity_outputs/sens_f12perm_low/VOLVE_2016.SMSPEC",
    "sens_f12perm_high": ROOT / "work/sensitivity_outputs/sens_f12perm_high/VOLVE_2016.SMSPEC",
    "sens_northpv_low": ROOT / "work/sensitivity_outputs/sens_northpv_low/VOLVE_2016.SMSPEC",
    "sens_northpv_high": ROOT / "work/sensitivity_outputs/sens_northpv_high/VOLVE_2016.SMSPEC",
}

required = [
    "TIME",
    "FOPT",
    "FWPT",
    "FGPT",
    "FPR",
    "FOPR",
    "FWPR",
    "WOPR:P-F-12",
    "WWCT:P-F-12",
    "WBHP:P-F-12",
]

optional = [
    "WOPT:P-F-12",
    "WWPT:P-F-12",
    "WGPT:P-F-12",
]

outdir = (
    args.output_dir.resolve()
    if args.output_dir is not None
    else ROOT / "analysis"
)
outdir.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------
# Check files
# -----------------------------------------------------
for name, smspec in cases.items():
    if not smspec.exists():
        raise FileNotFoundError(f"{name}: missing {smspec}")

# -----------------------------------------------------
# Determine optional vectors available in ALL cases
# -----------------------------------------------------
vector_lists = {}

for name, smspec in cases.items():
    result = subprocess.run(
        ["summary", "-l", str(smspec)],
        capture_output=True,
        text=True,
        check=True,
    )
    vector_lists[name] = result.stdout + result.stderr

common_optional = [
    vec for vec in optional
    if all(vec in vector_lists[name] for name in cases)
]

vectors = required + common_optional

print("===================================================")
print(" VECTORS TO EXTRACT")
print("===================================================")

for vec in vectors:
    print(vec)

if common_optional:
    print("\nOptional cumulative F-12 vectors found:")
    for vec in common_optional:
        print("  ", vec)
else:
    print("\nNo common optional F-12 cumulative vectors found.")

# -----------------------------------------------------
# Extract report-step data
# -----------------------------------------------------
all_rows = {}

for name, smspec in cases.items():

    cmd = [
        "summary",
        "-r",
        "-n",
        str(smspec),
        *vectors,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    rows = []

    for line in result.stdout.splitlines():

        parts = line.split()

        if len(parts) != len(vectors):
            continue

        try:
            values = [float(x) for x in parts]
        except ValueError:
            continue

        rows.append(dict(zip(vectors, values)))

    if not rows:
        raise RuntimeError(f"No numerical rows extracted for {name}")

    all_rows[name] = rows

    print(
        f"{name:20s} "
        f"rows={len(rows):3d} "
        f"first_day={rows[0]['TIME']:.1f} "
        f"last_day={rows[-1]['TIME']:.1f}"
    )

# -----------------------------------------------------
# Check time alignment against BASE
# -----------------------------------------------------
base_time = [r["TIME"] for r in all_rows["BASE"]]

print("\n===================================================")
print(" TIME ALIGNMENT CHECK")
print("===================================================")

for name, rows in all_rows.items():

    times = [r["TIME"] for r in rows]

    aligned = (
        len(times) == len(base_time)
        and all(
            math.isclose(a, b, rel_tol=0.0, abs_tol=1e-8)
            for a, b in zip(times, base_time)
        )
    )

    print(f"{name:20s} aligned_with_BASE = {aligned}")

# -----------------------------------------------------
# Save complete compact time-series table
# -----------------------------------------------------
timeseries_file = outdir / "sensitivity_timeseries_all_cases.csv"

with open(timeseries_file, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow(["CASE"] + vectors)

    for name, rows in all_rows.items():
        for row in rows:
            writer.writerow(
                [name] + [row[v] for v in vectors]
            )

# -----------------------------------------------------
# Final report-step metrics
# -----------------------------------------------------
final_metrics = [
    "FOPT",
    "FWPT",
    "FGPT",
    "FPR",
]

for vec in common_optional:
    final_metrics.append(vec)

final_file = outdir / "sensitivity_final_metrics.csv"

with open(final_file, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow(
        ["CASE", "FINAL_DAY"] + final_metrics
    )

    for name, rows in all_rows.items():

        row = rows[-1]

        writer.writerow(
            [name, row["TIME"]] +
            [row[m] for m in final_metrics]
        )

# -----------------------------------------------------
# Differences relative to BASE
# -----------------------------------------------------
base_final = all_rows["BASE"][-1]

effects_file = outdir / "sensitivity_effects_vs_base.csv"

with open(effects_file, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "CASE",
        "METRIC",
        "BASE_VALUE",
        "CASE_VALUE",
        "DELTA",
        "DELTA_PERCENT",
    ])

    for name, rows in all_rows.items():

        if name == "BASE":
            continue

        case_final = rows[-1]

        for metric in final_metrics:

            base_value = base_final[metric]
            case_value = case_final[metric]

            delta = case_value - base_value

            if abs(base_value) > 1e-30:
                delta_pct = 100.0 * delta / base_value
            else:
                delta_pct = float("nan")

            writer.writerow([
                name,
                metric,
                base_value,
                case_value,
                delta,
                delta_pct,
            ])

# -----------------------------------------------------
# F-12 diagnostic metrics over whole history
# -----------------------------------------------------
diag_file = outdir / "sensitivity_f12_diagnostics.csv"

with open(diag_file, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "CASE",
        "PEAK_WOPR_F12",
        "MAX_WWCT_F12",
        "MIN_WBHP_F12",
    ])

    for name, rows in all_rows.items():

        peak_wopr = max(r["WOPR:P-F-12"] for r in rows)
        max_wwct = max(r["WWCT:P-F-12"] for r in rows)
        min_wbhp = min(r["WBHP:P-F-12"] for r in rows)

        writer.writerow([
            name,
            peak_wopr,
            max_wwct,
            min_wbhp,
        ])

# -----------------------------------------------------
# Print final values
# -----------------------------------------------------
print("\n===================================================")
print(" FINAL REPORT-STEP METRICS")
print("===================================================")

header = (
    f"{'CASE':20s} "
    f"{'FOPT':>14s} "
    f"{'FWPT':>14s} "
    f"{'FGPT':>14s} "
    f"{'FPR':>12s}"
)

print(header)

for name, rows in all_rows.items():

    r = rows[-1]

    print(
        f"{name:20s} "
        f"{r['FOPT']:14.3f} "
        f"{r['FWPT']:14.3f} "
        f"{r['FGPT']:14.3f} "
        f"{r['FPR']:12.4f}"
    )

# -----------------------------------------------------
# Print FOPT sensitivity ranking
# -----------------------------------------------------
print("\n===================================================")
print(" FINAL FOPT CHANGE RELATIVE TO BASE")
print("===================================================")

base_fopt = base_final["FOPT"]

ranking = []

for name, rows in all_rows.items():

    if name == "BASE":
        continue

    value = rows[-1]["FOPT"]

    pct = 100.0 * (value - base_fopt) / base_fopt

    ranking.append((abs(pct), name, value, pct))

for _, name, value, pct in sorted(ranking, reverse=True):

    print(
        f"{name:20s} "
        f"FOPT={value:14.3f} "
        f"Delta={pct:+9.4f}%"
    )

print("\n===================================================")
print(" OUTPUT FILES")
print("===================================================")

for p in [
    timeseries_file,
    final_file,
    effects_file,
    diag_file,
]:
    print(p)

print("\nEXTRACTION COMPLETE")
