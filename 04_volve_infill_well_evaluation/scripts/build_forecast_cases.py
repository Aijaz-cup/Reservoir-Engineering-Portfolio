from pathlib import Path
from datetime import date
import csv

BASE_DIR = Path(
    "/mnt/c/Users/ADMIN/Desktop/OPM/Project_04_Volve_Base_Model"
)

REPO = Path(
    "/mnt/c/Users/ADMIN/Desktop/GitHub/"
    "Reservoir-Engineering-Portfolio/"
    "04_volve_infill_well_evaluation"
)

SOURCE = BASE_DIR / "VOLVE_2016.DATA"

# ---------------------------------------------------------------------
# DETERMINISTIC FORECAST ASSUMPTION
# ---------------------------------------------------------------------

FORECAST_BHP_BAR = 300.0
FORECAST_END = date(2021, 10, 1)

CASES = {
    "BASE": None,

    "A": {
        "well": "INF-A",
        "I": 70,
        "J": 21,
        "K1": 1,
        "K2": 4,
        "reason": (
            "Highest-quality screened opportunity; "
            "K5 excluded because of high late-life water saturation."
        ),
    },

    "B": {
        "well": "INF-B",
        "I": 66,
        "J": 32,
        "K1": 59,
        "K2": 63,
        "reason": (
            "Water-swept comparison candidate with remaining oil "
            "and adequate local reservoir quality."
        ),
    },

    "C": {
        "well": "INF-C",
        "I": 46,
        "J": 27,
        "K1": 59,
        "K2": 63,
        "reason": (
            "High remaining oil saturation and minimal sweep, "
            "but smaller connected oil-volume opportunity."
        ),
    },
}

# ---------------------------------------------------------------------
# READ ORIGINAL DECK
# ---------------------------------------------------------------------

text = SOURCE.read_text(errors="ignore")
lines = text.splitlines(keepends=True)

prediction_seen = False
first_prediction_end = None

for idx, line in enumerate(lines):

    if "PREDICTION" in line.upper():
        prediction_seen = True

    if (
        prediction_seen
        and line.strip().upper() == "END"
    ):
        first_prediction_end = idx
        break

if first_prediction_end is None:
    raise RuntimeError(
        "Could not locate first END after PREDICTION section."
    )

# Preserve everything up to but not including first END.
# This already includes:
#
# DATES
#   1 'OCT' 2016 /
# /
#
forecast_prefix = "".join(
    lines[:first_prediction_end]
).rstrip() + "\n\n"

# ---------------------------------------------------------------------
# SUMMARY OUTPUT FOR NEW WELLS
# Insert immediately before SCHEDULE.
# ---------------------------------------------------------------------

def add_candidate_summary(deck_text, well):

    schedule_pos = deck_text.upper().find("\nSCHEDULE")

    if schedule_pos < 0:
        raise RuntimeError("Could not find SCHEDULE section.")

    summary = f"""
-- ================================================================
-- PROJECT 04: SUMMARY OUTPUT FOR {well}
-- ================================================================

WOPR
 '{well}' /
/

WWPR
 '{well}' /
/

WWCT
 '{well}' /
/

WBHP
 '{well}' /
/

"""

    return (
        deck_text[:schedule_pos]
        + summary
        + deck_text[schedule_pos:]
    )

# ---------------------------------------------------------------------
# NEW INFILL PRODUCER
# ---------------------------------------------------------------------

def candidate_block(cfg):

    well = cfg["well"]
    I = cfg["I"]
    J = cfg["J"]
    K1 = cfg["K1"]
    K2 = cfg["K2"]

    return f"""
-- ================================================================
-- PROJECT 04 INFILL WELL
-- Deterministic screening case
-- Common producer control: BHP = {FORECAST_BHP_BAR:.1f} bar
-- ================================================================

WELSPECS
 '{well}'  'SRAR'  {I}  {J}  1*  'OIL'  7* /
/

COMPDAT
 '{well}'  {I}  {J}  {K1}  {K2}  'OPEN'  2*  0.216  3*  'Z' /
/

WCONPROD
 '{well}'  'OPEN'  'BHP'  5*  {FORECAST_BHP_BAR:.1f} /
/

"""

# ---------------------------------------------------------------------
# QUARTERLY FORECAST REPORT DATES
# 1 Oct 2016 already exists in original deck.
# ---------------------------------------------------------------------

forecast_dates = []

year = 2017

while True:

    for month_name, month in [
        ("JAN", 1),
        ("APR", 4),
        ("JUL", 7),
        ("OCT", 10),
    ]:

        d = date(year, month, 1)

        if d > FORECAST_END:
            break

        forecast_dates.append(
            f"""DATES
 1 '{month_name}' {year} /
/

"""
        )

    if date(year, 10, 1) >= FORECAST_END:
        break

    year += 1

future_schedule = "".join(forecast_dates)

# ---------------------------------------------------------------------
# CREATE CASES
# ---------------------------------------------------------------------

created = []

for case_name, cfg in CASES.items():

    deck = forecast_prefix

    if cfg is not None:

        # Add well-specific SUMMARY vectors.
        deck = add_candidate_summary(
            deck,
            cfg["well"]
        )

        # The original deck already reached 1 Oct 2016.
        # Well therefore starts at this report date.
        deck += candidate_block(cfg)

    deck += future_schedule
    deck += "END\n"

    out = BASE_DIR / f"P04_FORECAST_{case_name}.DATA"

    out.write_text(deck)

    created.append(out)

# ---------------------------------------------------------------------
# DESIGN AUDIT CSV
# ---------------------------------------------------------------------

results_dir = REPO / "results"
results_dir.mkdir(parents=True, exist_ok=True)

design_csv = results_dir / "final_forecast_case_design.csv"

with design_csv.open("w", newline="") as f:

    fields = [
        "case",
        "well",
        "I",
        "J",
        "K1",
        "K2",
        "control",
        "bhp_bar",
        "forecast_start",
        "forecast_end",
        "reason",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields
    )

    writer.writeheader()

    writer.writerow({
        "case": "BASE",
        "well": "",
        "I": "",
        "J": "",
        "K1": "",
        "K2": "",
        "control": "No new infill well",
        "bhp_bar": "",
        "forecast_start": "2016-10-01",
        "forecast_end": FORECAST_END.isoformat(),
        "reason": "Reference case",
    })

    for case_name in ["A", "B", "C"]:

        cfg = CASES[case_name]

        writer.writerow({
            "case": case_name,
            "well": cfg["well"],
            "I": cfg["I"],
            "J": cfg["J"],
            "K1": cfg["K1"],
            "K2": cfg["K2"],
            "control": "BHP",
            "bhp_bar": FORECAST_BHP_BAR,
            "forecast_start": "2016-10-01",
            "forecast_end": FORECAST_END.isoformat(),
            "reason": cfg["reason"],
        })

print("=" * 78)
print("PROJECT 04 — FORECAST CASE BUILDER")
print("=" * 78)

print("\nOriginal master deck left unchanged:")
print(SOURCE)

print("\nCreated:")

for p in created:
    print(" ", p.name)

print("\nDesign CSV:")
print(design_csv)

print("\nForecast assumption:")
print(f"  Start : 2016-10-01")
print(f"  End   : {FORECAST_END}")
print(f"  BHP   : {FORECAST_BHP_BAR:.1f} bar")

print("\nVerification:")

for p in created:

    d = p.read_text(errors="ignore")

    n_end = sum(
        1 for line in d.splitlines()
        if line.strip().upper() == "END"
    )

    print(
        f"  {p.name:24s}"
        f" END_count={n_end}"
    )

print("\nBUILD COMPLETE")
