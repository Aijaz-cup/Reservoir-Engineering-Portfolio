from pathlib import Path
from datetime import timedelta, date
import csv
import math
import numpy as np

from opm.io.ecl import ESmry

# =====================================================================
# PROJECT 04 — FINAL FORECAST RESULT EXTRACTION
# =====================================================================

ROOT = Path("/mnt/c/Users/ADMIN/Desktop/OPM")
REPO = Path(
    "/mnt/c/Users/ADMIN/Desktop/GitHub/"
    "Reservoir-Engineering-Portfolio/"
    "04_volve_infill_well_evaluation"
)

RESULTS = REPO / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

FORECAST_START = date(2016, 10, 1)
FORECAST_END   = date(2021, 10, 1)

CASES = {
    "BASE": {
        "dir": ROOT / "Project_04_Forecast_BASE_FULL",
        "stem": "P04_FORECAST_BASE",
        "well": None,
    },
    "A": {
        "dir": ROOT / "Project_04_Forecast_A_FULL",
        "stem": "P04_FORECAST_A",
        "well": "INF-A",
    },
    "B": {
        "dir": ROOT / "Project_04_Forecast_B_FULL",
        "stem": "P04_FORECAST_B",
        "well": "INF-B",
    },
    "C": {
        "dir": ROOT / "Project_04_Forecast_C_FULL",
        "stem": "P04_FORECAST_C",
        "well": "INF-C",
    },
}


def finite(x):
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def value_or_nan(arr, idx):
    if arr is None:
        return float("nan")
    return float(arr[idx])


def safe_unit(smry, key):
    try:
        return str(smry.units(key))
    except Exception:
        return ""


def build_report_dates(smry, time_values):
    """
    Convert ECL summary TIME at report steps into calendar dates.
    """
    unit = safe_unit(smry, "TIME").upper()

    if "HOUR" in unit:
        day_factor = 1.0 / 24.0
    elif "YEAR" in unit:
        day_factor = 365.25
    else:
        # METRIC ECLIPSE summary TIME normally uses days.
        day_factor = 1.0

    start = smry.start_date

    return [
        (start + timedelta(days=float(t) * day_factor)).date()
        for t in time_values
    ]


def find_date_index(dates, target):
    exact = [i for i, d in enumerate(dates) if d == target]

    if exact:
        return exact[0]

    # Fallback to nearest report date if exact date is absent.
    return min(
        range(len(dates)),
        key=lambda i: abs((dates[i] - target).days)
    )


# =====================================================================
# LOAD CASES
# =====================================================================

loaded = {}

print("=" * 88)
print("PROJECT 04 — FINAL FORECAST RESULT EXTRACTION")
print("=" * 88)

for case, cfg in CASES.items():

    esmry_file = cfg["dir"] / f"{cfg['stem']}.ESMRY"

    if not esmry_file.exists():
        raise FileNotFoundError(esmry_file)

    smry = ESmry(str(esmry_file))

    keys = set(smry.keys())

    get_report = getattr(smry, "__get_at_rstep")

    def get_vector(key, _keys=keys, _get_report=get_report):
        """
        Case-bound summary-vector getter.

        _keys and _get_report are bound as default arguments here
        so every case keeps its own ESmry object instead of all
        closures referring to the final case in the loading loop.
        """
        if key not in _keys:
            return None

        return np.asarray(
            _get_report(key),
            dtype=float
        )

    if "TIME" not in keys:
        raise RuntimeError(
            f"{case}: TIME summary vector not found"
        )

    TIME = get_vector("TIME")
    dates = build_report_dates(smry, TIME)

    i0 = find_date_index(dates, FORECAST_START)
    i1 = find_date_index(dates, FORECAST_END)

    print()
    print(f"CASE {case}")
    print("-" * 60)
    print("ESMRY        :", esmry_file)
    print("Report steps :", len(TIME))
    print("Start match  :", dates[i0], "index", i0)
    print("End match    :", dates[i1], "index", i1)

    if dates[i0] != FORECAST_START:
        print(
            "WARNING: forecast start exact date not found;"
            " nearest report date used."
        )

    if dates[i1] != FORECAST_END:
        print(
            "WARNING: forecast end exact date not found;"
            " nearest report date used."
        )

    loaded[case] = {
        "cfg": cfg,
        "smry": smry,
        "keys": keys,
        "get": get_vector,
        "dates": dates,
        "i0": i0,
        "i1": i1,
    }


# =====================================================================
# VECTOR UNITS
# =====================================================================

unit_keys = [
    "FOPT",
    "FWPT",
    "FOPR",
    "FWPR",
    "FPR",
    "WOPT:INF-A",
    "WOPR:INF-A",
    "WWPR:INF-A",
    "WWCT:INF-A",
    "WBHP:INF-A",
]

units_csv = RESULTS / "summary_vector_units.csv"

with units_csv.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["vector", "unit"])

    sma = loaded["A"]["smry"]

    for key in unit_keys:
        writer.writerow([
            key,
            safe_unit(sma, key)
        ])


# =====================================================================
# FIELD + CANDIDATE PERFORMANCE
# =====================================================================

rows = []

for case in ["BASE", "A", "B", "C"]:

    D = loaded[case]

    get = D["get"]
    i0 = D["i0"]
    i1 = D["i1"]

    FOPT = get("FOPT")
    FWPT = get("FWPT")
    FOPR = get("FOPR")
    FPR  = get("FPR")

    if FOPT is None:
        raise RuntimeError(f"{case}: FOPT missing")

    if FWPT is None:
        raise RuntimeError(f"{case}: FWPT missing")

    forecast_oil = (
        float(FOPT[i1]) -
        float(FOPT[i0])
    )

    forecast_water = (
        float(FWPT[i1]) -
        float(FWPT[i0])
    )

    row = {
        "case": case,
        "candidate_well": D["cfg"]["well"] or "",
        "forecast_start": str(D["dates"][i0]),
        "forecast_end": str(D["dates"][i1]),

        "FOPT_start": float(FOPT[i0]),
        "FOPT_end": float(FOPT[i1]),
        "field_forecast_oil": forecast_oil,

        "FWPT_start": float(FWPT[i0]),
        "FWPT_end": float(FWPT[i1]),
        "field_forecast_water": forecast_water,

        "FPR_start": value_or_nan(FPR, i0),
        "FPR_end": value_or_nan(FPR, i1),

        "candidate_WOPT_forecast": float("nan"),
        "candidate_peak_WOPR": float("nan"),
        "candidate_end_WOPR": float("nan"),

        "candidate_first_active_WWCT": float("nan"),
        "candidate_latest_active_WWCT": float("nan"),

        "candidate_min_WBHP": float("nan"),
        "candidate_mean_active_WBHP": float("nan"),
    }

    well = D["cfg"]["well"]

    if well:

        WOPT = get(f"WOPT:{well}")
        WOPR = get(f"WOPR:{well}")
        WWPR = get(f"WWPR:{well}")
        WWCT = get(f"WWCT:{well}")
        WBHP = get(f"WBHP:{well}")

        if WOPT is not None:
            row["candidate_WOPT_forecast"] = (
                float(WOPT[i1]) -
                float(WOPT[i0])
            )

        if WOPR is not None:

            wopr_fore = WOPR[i0:i1 + 1]

            row["candidate_peak_WOPR"] = float(
                np.nanmax(wopr_fore)
            )

            row["candidate_end_WOPR"] = float(
                WOPR[i1]
            )

            # Determine when the well was actually flowing.
            if WWPR is not None:
                activity = (
                    np.abs(WOPR[i0:i1 + 1])
                    +
                    np.abs(WWPR[i0:i1 + 1])
                )
            else:
                activity = np.abs(
                    WOPR[i0:i1 + 1]
                )

            active_local = np.where(
                activity > 1.0e-8
            )[0]

            if len(active_local):

                active_global = (
                    active_local + i0
                )

                first_idx = int(
                    active_global[0]
                )

                last_idx = int(
                    active_global[-1]
                )

                if WWCT is not None:
                    row[
                        "candidate_first_active_WWCT"
                    ] = float(
                        WWCT[first_idx]
                    )

                    row[
                        "candidate_latest_active_WWCT"
                    ] = float(
                        WWCT[last_idx]
                    )

                if WBHP is not None:

                    vals = WBHP[
                        active_global
                    ]

                    row[
                        "candidate_min_WBHP"
                    ] = float(
                        np.nanmin(vals)
                    )

                    row[
                        "candidate_mean_active_WBHP"
                    ] = float(
                        np.nanmean(vals)
                    )

    rows.append(row)


# =====================================================================
# INCREMENTAL FIELD RESPONSE VS BASE
# =====================================================================

base = next(
    r for r in rows
    if r["case"] == "BASE"
)

for row in rows:

    if row["case"] == "BASE":

        row["delta_field_oil_vs_base"] = 0.0
        row["delta_field_water_vs_base"] = 0.0
        row["water_per_incremental_oil"] = float("nan")
        row["interference_oil_proxy"] = float("nan")
        row["incremental_fraction_of_candidate_oil"] = float("nan")

        continue

    delta_oil = (
        row["field_forecast_oil"]
        -
        base["field_forecast_oil"]
    )

    delta_water = (
        row["field_forecast_water"]
        -
        base["field_forecast_water"]
    )

    row["delta_field_oil_vs_base"] = delta_oil
    row["delta_field_water_vs_base"] = delta_water

    if abs(delta_oil) > 1.0e-12:
        row["water_per_incremental_oil"] = (
            delta_water / delta_oil
        )
    else:
        row["water_per_incremental_oil"] = float("nan")

    well_oil = row[
        "candidate_WOPT_forecast"
    ]

    if finite(well_oil):

        # Candidate well oil minus net field incremental oil.
        #
        # This is an interference/displacement proxy,
        # not an exact direct measurement of cannibalisation.
        row["interference_oil_proxy"] = (
            well_oil - delta_oil
        )

        if abs(well_oil) > 1.0e-12:
            row[
                "incremental_fraction_of_candidate_oil"
            ] = delta_oil / well_oil
        else:
            row[
                "incremental_fraction_of_candidate_oil"
            ] = float("nan")

    else:
        row["interference_oil_proxy"] = float("nan")
        row[
            "incremental_fraction_of_candidate_oil"
        ] = float("nan")


# =====================================================================
# SAVE FORECAST COMPARISON
# =====================================================================

comparison_csv = (
    RESULTS /
    "final_forecast_comparison.csv"
)

fieldnames = list(rows[0].keys())

with comparison_csv.open(
    "w",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)


# =====================================================================
# REPORT-STEP TIME SERIES
# =====================================================================

timeseries_csv = (
    RESULTS /
    "final_forecast_timeseries.csv"
)

ts_fields = [
    "case",
    "date",
    "FOPT",
    "FWPT",
    "FOPR",
    "FPR",
    "candidate_well",
    "WOPT",
    "WOPR",
    "WWPR",
    "WWCT",
    "WBHP",
]

with timeseries_csv.open(
    "w",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=ts_fields
    )

    writer.writeheader()

    for case in ["BASE", "A", "B", "C"]:

        D = loaded[case]

        get = D["get"]
        i0 = D["i0"]
        i1 = D["i1"]

        FOPT = get("FOPT")
        FWPT = get("FWPT")
        FOPR = get("FOPR")
        FPR  = get("FPR")

        well = D["cfg"]["well"]

        if well:
            WOPT = get(f"WOPT:{well}")
            WOPR = get(f"WOPR:{well}")
            WWPR = get(f"WWPR:{well}")
            WWCT = get(f"WWCT:{well}")
            WBHP = get(f"WBHP:{well}")
        else:
            WOPT = WOPR = WWPR = WWCT = WBHP = None

        for idx in range(
            i0,
            i1 + 1
        ):

            writer.writerow({
                "case": case,
                "date": str(
                    D["dates"][idx]
                ),

                "FOPT": value_or_nan(
                    FOPT, idx
                ),

                "FWPT": value_or_nan(
                    FWPT, idx
                ),

                "FOPR": value_or_nan(
                    FOPR, idx
                ),

                "FPR": value_or_nan(
                    FPR, idx
                ),

                "candidate_well": (
                    well or ""
                ),

                "WOPT": value_or_nan(
                    WOPT, idx
                ),

                "WOPR": value_or_nan(
                    WOPR, idx
                ),

                "WWPR": value_or_nan(
                    WWPR, idx
                ),

                "WWCT": value_or_nan(
                    WWCT, idx
                ),

                "WBHP": value_or_nan(
                    WBHP, idx
                ),
            })


# =====================================================================
# EXISTING-WELL INTERFERENCE
# =====================================================================

interference_rows = []

BASE = loaded["BASE"]

base_wopt_keys = {
    k for k in BASE["keys"]
    if k.startswith("WOPT:")
}

for case in ["A", "B", "C"]:

    D = loaded[case]

    candidate = D["cfg"]["well"]

    case_wopt_keys = {
        k for k in D["keys"]
        if k.startswith("WOPT:")
    }

    common = sorted(
        base_wopt_keys &
        case_wopt_keys
    )

    for key in common:

        well = key.split(
            ":",
            1
        )[1]

        if well == candidate:
            continue

        b = BASE["get"](key)
        c = D["get"](key)

        if b is None or c is None:
            continue

        b_inc = (
            float(b[BASE["i1"]])
            -
            float(b[BASE["i0"]])
        )

        c_inc = (
            float(c[D["i1"]])
            -
            float(c[D["i0"]])
        )

        delta = c_inc - b_inc

        # Keep relevant producing wells / responses.
        if (
            abs(b_inc) > 1.0e-8
            or
            abs(c_inc) > 1.0e-8
            or
            abs(delta) > 1.0e-8
        ):

            interference_rows.append({
                "case": case,
                "candidate_well": candidate,
                "existing_well": well,
                "base_forecast_oil": b_inc,
                "candidate_case_forecast_oil": c_inc,
                "delta_existing_well_oil": delta,
            })


interference_csv = (
    RESULTS /
    "existing_well_interference.csv"
)

if interference_rows:

    with interference_csv.open(
        "w",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(
                interference_rows[0].keys()
            )
        )

        writer.writeheader()
        writer.writerows(
            interference_rows
        )


# =====================================================================
# CONSOLE REPORT
# =====================================================================

print()
print("=" * 88)
print("FINAL FIELD FORECAST COMPARISON")
print("=" * 88)

print(
    f"{'CASE':<6}"
    f"{'FIELD OIL':>16}"
    f"{'Δ OIL vs BASE':>18}"
    f"{'Δ WATER':>16}"
    f"{'WELL OIL':>16}"
    f"{'PEAK WOPR':>16}"
)

for r in rows:

    def fmt(v):
        if finite(v):
            return f"{float(v):,.3f}"
        return "N/A"

    print(
        f"{r['case']:<6}"
        f"{fmt(r['field_forecast_oil']):>16}"
        f"{fmt(r['delta_field_oil_vs_base']):>18}"
        f"{fmt(r['delta_field_water_vs_base']):>16}"
        f"{fmt(r['candidate_WOPT_forecast']):>16}"
        f"{fmt(r['candidate_peak_WOPR']):>16}"
    )


print()
print("=" * 88)
print("PRELIMINARY RANKING — INCREMENTAL FIELD OIL")
print("=" * 88)

for rank, r in enumerate(
    ranked,
    start=1
):

    print(
        f"{rank}. Candidate {r['case']} "
        f"({r['candidate_well']}): "
        f"ΔNp = "
        f"{r['delta_field_oil_vs_base']:,.3f}"
    )


print()
print("=" * 88)
print("FILES WRITTEN")
print("=" * 88)

print(comparison_csv)
print(timeseries_csv)
print(units_csv)
print(ranking_csv)

if interference_rows:
    print(interference_csv)

print()
print("EXTRACTION COMPLETE")
