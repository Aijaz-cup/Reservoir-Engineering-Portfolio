"""Audit and prepare the Volve monthly production dataset for DCA screening.

The workflow preserves the raw workbook, validates source schema and units,
checks data integrity, derives surveillance metrics, reconciles monthly totals
against independently aggregated daily records, and writes reproducible audit
outputs. No raw source values are edited in place.
"""

from pathlib import Path
import hashlib

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = PROJECT_DIR / "data" / "raw" / "Volve production data.xlsx"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "report"

MONTHLY_SHEET = "Monthly Production Data"
DAILY_SHEET = "Daily Production Data"

EXPECTED_MONTHLY_COLUMNS = [
    "Wellbore name",
    "NPDCode",
    "Year",
    "Month",
    "On Stream",
    "Oil",
    "Gas",
    "Water",
    "GI",
    "WI",
]

EXPECTED_UNITS = {
    "On Stream": "hrs",
    "Oil": "Sm3",
    "Gas": "Sm3",
    "Water": "Sm3",
    "GI": "Sm3",
    "WI": "Sm3",
}

NUMERIC_COLUMNS = [
    "NPDCode",
    "Year",
    "Month",
    "On Stream",
    "Oil",
    "Gas",
    "Water",
    "GI",
    "WI",
]


def sha256sum(path: Path) -> str:
    """Return the SHA-256 checksum of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def require_columns(
    df: pd.DataFrame,
    required_columns,
    label: str,
) -> None:
    """Raise a clear error when required source columns are missing."""

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "{} is missing required columns: {}".format(
                label,
                missing,
            )
        )


def load_monthly_data():
    """Read, validate, and clean the monthly worksheet."""

    raw = pd.read_excel(
        DATA_FILE,
        sheet_name=MONTHLY_SHEET,
        engine="openpyxl",
    )

    require_columns(
        raw,
        EXPECTED_MONTHLY_COLUMNS,
        MONTHLY_SHEET,
    )

    units = raw.iloc[0].copy()

    for column, expected_unit in EXPECTED_UNITS.items():
        actual_unit = units[column]

        if actual_unit != expected_unit:
            raise ValueError(
                "Unexpected unit for '{}': expected '{}', found '{}'".format(
                    column,
                    expected_unit,
                    actual_unit,
                )
            )

    # Row 1 contains units rather than a well-month observation.
    # The source workbook is not modified.
    df = raw.iloc[1:].copy().reset_index(drop=True)

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

    df["NPDCode"] = df["NPDCode"].astype("Int64")
    df["Year"] = df["Year"].astype("Int64")
    df["Month"] = df["Month"].astype("Int64")

    df["Date"] = pd.to_datetime(
        {
            "year": df["Year"],
            "month": df["Month"],
            "day": 1,
        },
        errors="raise",
    )

    return units, df


def validate_monthly_data(df: pd.DataFrame):
    """Run deterministic integrity checks on monthly source records."""

    issues = {}

    issues["missing_well_name"] = int(
        df["Wellbore name"].isna().sum()
    )

    issues["missing_date"] = int(
        df["Date"].isna().sum()
    )

    issues["duplicate_well_month"] = int(
        df.duplicated(
            subset=["Wellbore name", "Date"]
        ).sum()
    )

    nonnegative_columns = [
        "On Stream",
        "Oil",
        "Gas",
        "Water",
        "GI",
        "WI",
    ]

    issues["negative_values"] = int(
        sum(
            (df[column].dropna() < 0).sum()
            for column in nonnegative_columns
        )
    )

    nominal_month_hours = (
        df["Date"].dt.days_in_month.astype(float) * 24.0
    )

    excess_hours = (
        df["On Stream"] - nominal_month_hours
    )

    # The source contains a small number of records up to one hour above
    # 24 x calendar days. They are retained and reported, not corrected,
    # because the daily worksheet independently reconciles to the same totals.
    exception_mask = (
        (excess_hours > 1.0e-6)
        & (excess_hours <= 1.01)
    )

    hour_exceptions = df.loc[
        exception_mask,
        [
            "Wellbore name",
            "NPDCode",
            "Date",
            "On Stream",
        ],
    ].copy()

    hour_exceptions["Nominal Month Hours"] = (
        nominal_month_hours.loc[exception_mask].values
    )

    hour_exceptions["Excess Hours"] = (
        excess_hours.loc[exception_mask].values
    )

    issues["on_stream_hour_exceptions"] = int(
        exception_mask.sum()
    )

    issues["on_stream_over_nominal_by_more_than_one_hour"] = int(
        (excess_hours > 1.01).sum()
    )

    production_volume = (
        df[["Oil", "Gas", "Water"]]
        .fillna(0.0)
        .sum(axis=1)
    )

    injection_volume = (
        df[["GI", "WI"]]
        .fillna(0.0)
        .sum(axis=1)
    )

    issues["positive_production_without_onstream"] = int(
        (
            (production_volume > 0)
            & (df["On Stream"].fillna(0.0) <= 0)
        ).sum()
    )

    issues["positive_injection_without_onstream"] = int(
        (
            (injection_volume > 0)
            & (df["On Stream"].fillna(0.0) <= 0)
        ).sum()
    )

    hard_failure_checks = [
        "missing_well_name",
        "missing_date",
        "duplicate_well_month",
        "negative_values",
        "on_stream_over_nominal_by_more_than_one_hour",
        "positive_production_without_onstream",
        "positive_injection_without_onstream",
    ]

    if any(
        issues[key] != 0
        for key in hard_failure_checks
    ):
        raise ValueError(
            "Monthly production-data QC failed: {}".format(
                issues
            )
        )

    return issues, hour_exceptions


def add_engineering_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate rate and surveillance variables without altering source values."""

    df = df.copy()

    production_volume = (
        df[["Oil", "Gas", "Water"]]
        .fillna(0.0)
        .sum(axis=1)
    )

    injection_volume = (
        df[["GI", "WI"]]
        .fillna(0.0)
        .sum(axis=1)
    )

    df["Is Producer"] = production_volume > 0
    df["Is Injector"] = injection_volume > 0

    df["Calendar Days"] = (
        df["Date"].dt.days_in_month.astype(float)
    )

    df["Nominal Month Hours"] = (
        df["Calendar Days"] * 24.0
    )

    # Uptime is referenced to the nominal calendar-month duration.
    # Source records that exceed this duration by up to one hour are retained
    # unchanged and explicitly documented by the QC workflow rather than
    # being hidden through an adjusted denominator.
    df["Producing Days"] = (
        df["On Stream"] / 24.0
    )

    df["Uptime Fraction"] = (
        df["On Stream"]
        / df["Nominal Month Hours"]
    )

    valid_onstream = (
        df["On Stream"].fillna(0.0) > 0
    )

    for phase in ["Oil", "Gas", "Water"]:
        producing_rate_column = (
            "{} Rate Sm3/d".format(phase)
        )

        calendar_rate_column = (
            "{} Calendar Rate Sm3/d".format(phase)
        )

        df[producing_rate_column] = np.nan
        df[calendar_rate_column] = np.nan

        valid_phase = (
            valid_onstream
            & df[phase].notna()
        )

        df.loc[
            valid_phase,
            producing_rate_column,
        ] = (
            df.loc[valid_phase, phase]
            / df.loc[valid_phase, "Producing Days"]
        )

        valid_calendar = df[phase].notna()

        df.loc[
            valid_calendar,
            calendar_rate_column,
        ] = (
            df.loc[valid_calendar, phase]
            / df.loc[valid_calendar, "Calendar Days"]
        )

    liquid_volume = (
        df["Oil"].fillna(0.0)
        + df["Water"].fillna(0.0)
    )

    df["Water Cut"] = np.nan

    valid_liquid = liquid_volume > 0

    df.loc[
        valid_liquid,
        "Water Cut",
    ] = (
        df.loc[valid_liquid, "Water"].fillna(0.0)
        / liquid_volume.loc[valid_liquid]
    )

    df["GOR Sm3/Sm3"] = np.nan

    valid_oil = (
        df["Oil"].fillna(0.0) > 0
    )

    df.loc[
        valid_oil,
        "GOR Sm3/Sm3",
    ] = (
        df.loc[valid_oil, "Gas"]
        / df.loc[valid_oil, "Oil"]
    )

    return df


def crosscheck_daily_vs_monthly(monthly: pd.DataFrame):
    """Reconcile monthly source totals against independent daily aggregation."""

    daily = pd.read_excel(
        DATA_FILE,
        sheet_name=DAILY_SHEET,
        engine="openpyxl",
    )

    required_daily_columns = [
        "DATEPRD",
        "NPD_WELL_BORE_CODE",
        "ON_STREAM_HRS",
        "BORE_OIL_VOL",
        "BORE_GAS_VOL",
        "BORE_WAT_VOL",
        "BORE_WI_VOL",
    ]

    require_columns(
        daily,
        required_daily_columns,
        DAILY_SHEET,
    )

    daily["DATEPRD"] = pd.to_datetime(
        daily["DATEPRD"],
        errors="raise",
    )

    daily["NPD_WELL_BORE_CODE"] = pd.to_numeric(
        daily["NPD_WELL_BORE_CODE"],
        errors="raise",
    ).astype("Int64")

    daily["Date"] = (
        daily["DATEPRD"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    # min_count=1 preserves the distinction between:
    #   all source values missing -> NaN
    #   actual measured/recorded zero -> 0
    daily_monthly = (
        daily.groupby(
            ["NPD_WELL_BORE_CODE", "Date"],
            as_index=False,
        )
        .agg(
            Daily_On_Stream=(
                "ON_STREAM_HRS",
                lambda x: x.sum(min_count=1),
            ),
            Daily_Oil=(
                "BORE_OIL_VOL",
                lambda x: x.sum(min_count=1),
            ),
            Daily_Gas=(
                "BORE_GAS_VOL",
                lambda x: x.sum(min_count=1),
            ),
            Daily_Water=(
                "BORE_WAT_VOL",
                lambda x: x.sum(min_count=1),
            ),
            Daily_WI=(
                "BORE_WI_VOL",
                lambda x: x.sum(min_count=1),
            ),
        )
    )

    merged = monthly.merge(
        daily_monthly,
        left_on=["NPDCode", "Date"],
        right_on=["NPD_WELL_BORE_CODE", "Date"],
        how="left",
        validate="one_to_one",
    )

    comparisons = [
        ("On Stream", "Daily_On_Stream"),
        ("Oil", "Daily_Oil"),
        ("Gas", "Daily_Gas"),
        ("Water", "Daily_Water"),
        ("WI", "Daily_WI"),
    ]

    results = []
    representation_rows = []

    for monthly_column, daily_column in comparisons:
        monthly_values = merged[monthly_column]
        daily_values = merged[daily_column]

        both_present = (
            monthly_values.notna()
            & daily_values.notna()
        )

        zero_null_difference = (
            (
                monthly_values.eq(0)
                & daily_values.isna()
            )
            | (
                daily_values.eq(0)
                & monthly_values.isna()
            )
        )

        unexpected_missingness = (
            monthly_values.isna()
            ^ daily_values.isna()
        ) & (~zero_null_difference)

        numeric_mismatch = pd.Series(
            False,
            index=merged.index,
        )

        numeric_mismatch.loc[both_present] = (
            ~np.isclose(
                monthly_values.loc[both_present].astype(float),
                daily_values.loc[both_present].astype(float),
                rtol=1.0e-9,
                atol=1.0e-6,
            )
        )

        differences = (
            monthly_values.loc[both_present].astype(float)
            - daily_values.loc[both_present].astype(float)
        ).abs()

        results.append(
            {
                "Variable": monthly_column,
                "Matched Rows": int(both_present.sum()),
                "Numeric Mismatches": int(numeric_mismatch.sum()),
                "Null/Zero Representation Differences": int(
                    zero_null_difference.sum()
                ),
                "Unexpected Missingness Differences": int(
                    unexpected_missingness.sum()
                ),
                "Maximum Absolute Difference": (
                    float(differences.max())
                    if len(differences)
                    else np.nan
                ),
            }
        )

        for index in merged.index[zero_null_difference]:
            representation_rows.append(
                {
                    "Variable": monthly_column,
                    "Wellbore name": merged.at[
                        index,
                        "Wellbore name",
                    ],
                    "Date": merged.at[index, "Date"],
                    "Monthly Value": merged.at[
                        index,
                        monthly_column,
                    ],
                    "Daily Aggregated Value": merged.at[
                        index,
                        daily_column,
                    ],
                    "Interpretation": (
                        "Zero-versus-null representation difference"
                    ),
                }
            )

    result = pd.DataFrame(results)

    representation_differences = pd.DataFrame(
        representation_rows,
        columns=[
            "Variable",
            "Wellbore name",
            "Date",
            "Monthly Value",
            "Daily Aggregated Value",
            "Interpretation",
        ],
    )

    hard_failures = int(
        result["Numeric Mismatches"].sum()
        + result[
            "Unexpected Missingness Differences"
        ].sum()
    )

    if hard_failures != 0:
        raise ValueError(
            "Monthly-to-daily reconciliation failed:\n{}".format(
                result.to_string(index=False)
            )
        )

    return result, representation_differences


def build_well_screening(df: pd.DataFrame) -> pd.DataFrame:
    """Build an engineering screening table for producer/injector histories."""

    rows = []

    for well, group in df.groupby(
        "Wellbore name",
        sort=True,
    ):
        producing = group.loc[
            group["Is Producer"]
        ]

        injecting = group.loc[
            group["Is Injector"]
        ]

        has_production = not producing.empty
        has_injection = not injecting.empty

        first_production = (
            producing["Date"].min()
            if has_production
            else pd.NaT
        )

        last_production = (
            producing["Date"].max()
            if has_production
            else pd.NaT
        )

        first_injection = (
            injecting["Date"].min()
            if has_injection
            else pd.NaT
        )

        last_injection = (
            injecting["Date"].max()
            if has_injection
            else pd.NaT
        )

        if has_production and has_injection:
            if last_injection <= first_production:
                role = "Injector -> Producer"
            elif last_production <= first_injection:
                role = "Producer -> Injector"
            else:
                role = "Producer/Injector"
        elif has_production:
            role = "Producer"
        elif has_injection:
            role = "Injector"
        else:
            role = "Inactive/Unknown"

        rows.append(
            {
                "Wellbore name": well,
                "NPDCode": int(
                    group["NPDCode"].iloc[0]
                ),
                "Role": role,
                "First Record": group["Date"].min(),
                "Last Record": group["Date"].max(),
                "First Production": first_production,
                "Last Production": last_production,
                "First Injection": first_injection,
                "Last Injection": last_injection,
                "Records": int(len(group)),
                "Producing Months": int(
                    group["Is Producer"].sum()
                ),
                "Injection Months": int(
                    group["Is Injector"].sum()
                ),
                "Oil Sm3": float(
                    group["Oil"].fillna(0.0).sum()
                ),
                "Gas Sm3": float(
                    group["Gas"].fillna(0.0).sum()
                ),
                "Water Sm3": float(
                    group["Water"].fillna(0.0).sum()
                ),
                "Water Injection Sm3": float(
                    group["WI"].fillna(0.0).sum()
                ),
                "Peak Oil Rate Sm3/d": (
                    float(
                        group["Oil Rate Sm3/d"].max()
                    )
                    if group["Oil Rate Sm3/d"].notna().any()
                    else np.nan
                ),
            }
        )

    screening = pd.DataFrame(rows)

    screening = screening.round(
        {
            "Oil Sm3": 2,
            "Gas Sm3": 2,
            "Water Sm3": 2,
            "Water Injection Sm3": 2,
            "Peak Oil Rate Sm3/d": 2,
        }
    )

    return screening


def write_markdown_audit(
    sha256: str,
    monthly: pd.DataFrame,
    qc: dict,
    crosscheck: pd.DataFrame,
    screening: pd.DataFrame,
) -> Path:
    """Write a concise interview-facing Markdown audit summary."""

    output_path = REPORT_DIR / "DATA_AUDIT.md"

    numeric_mismatches = int(
        crosscheck["Numeric Mismatches"].sum()
    )

    unexpected_missingness = int(
        crosscheck[
            "Unexpected Missingness Differences"
        ].sum()
    )

    representation_count = int(
        crosscheck[
            "Null/Zero Representation Differences"
        ].sum()
    )

    producer_count = int(
        screening["Role"].str.contains(
            "Producer",
            regex=False,
        ).sum()
    )

    injector_related_count = int(
        screening["Role"].str.contains(
            "Injector",
            regex=False,
        ).sum()
    )

    lines = [
        "# Volve Production Data Audit",
        "",
        "## Purpose",
        "",
        (
            "Quality-control review performed before decline-curve analysis. "
            "The raw Equinor workbook is preserved unchanged; cleaning and "
            "derived calculations are reproducible in "
            "`src/monthly_data_audit.py`."
        ),
        "",
        "## Source",
        "",
        "- Workbook: `Volve production data.xlsx`",
        "- Monthly sheet: `Monthly Production Data`",
        "- Daily sheet: `Daily Production Data`",
        "- SHA-256: `{}`".format(sha256),
        "",
        "## Dataset Summary",
        "",
        "- Clean monthly records: {:,}".format(len(monthly)),
        "- Wellbores: {}".format(
            monthly["Wellbore name"].nunique()
        ),
        "- Date range: {} to {}".format(
            monthly["Date"].min().date(),
            monthly["Date"].max().date(),
        ),
        "- Producer-related wellbores: {}".format(
            producer_count
        ),
        "- Injector-related wellbores: {}".format(
            injector_related_count
        ),
        "",
        "## Verified Source Units",
        "",
        "| Variable | Unit |",
        "|---|---|",
        "| On Stream | hrs |",
        "| Oil | Sm3 |",
        "| Gas | Sm3 |",
        "| Water | Sm3 |",
        "| Gas Injection | Sm3 |",
        "| Water Injection | Sm3 |",
        "",
        "## Quality-Control Result",
        "",
        "| Check | Result |",
        "|---|---:|",
        "| Missing well names | {} |".format(
            qc["missing_well_name"]
        ),
        "| Missing dates | {} |".format(
            qc["missing_date"]
        ),
        "| Duplicate well-month records | {} |".format(
            qc["duplicate_well_month"]
        ),
        "| Negative source values | {} |".format(
            qc["negative_values"]
        ),
        "| On-stream records > nominal month by <= 1 h | {} |".format(
            qc["on_stream_hour_exceptions"]
        ),
        "| On-stream records > nominal month by > 1 h | {} |".format(
            qc[
                "on_stream_over_nominal_by_more_than_one_hour"
            ]
        ),
        "| Production with non-positive on-stream time | {} |".format(
            qc[
                "positive_production_without_onstream"
            ]
        ),
        "| Injection with non-positive on-stream time | {} |".format(
            qc[
                "positive_injection_without_onstream"
            ]
        ),
        "| Daily/monthly numeric mismatches | {} |".format(
            numeric_mismatches
        ),
        "| Unexpected daily/monthly missingness differences | {} |".format(
            unexpected_missingness
        ),
        "| Documented zero/null representation differences | {} |".format(
            representation_count
        ),
        "",
        "## Interpretation Notes",
        "",
        (
            "- The unit row in the monthly worksheet is metadata, not a "
            "well-month observation, and is removed programmatically."
        ),
        (
            "- Monthly oil, gas, water, water-injection, and on-stream values "
            "numerically reconcile with independent aggregation of the daily "
            "worksheet within floating-point tolerance."
        ),
        (
            "- A small number of on-stream records exceed `24 x calendar days` "
            "by no more than one hour. These source values are retained, not "
            "corrected, because they reconcile with the daily sheet. The "
            "workflow does not impose an unverified timezone correction."
        ),
        (
            "- Zero-versus-null representation differences are documented "
            "separately from numerical mismatches so missing data are not "
            "silently converted to zero."
        ),
        "",
        "## Audit Status",
        "",
        (
            "**PASS - data are suitable for the next well-surveillance and "
            "DCA-screening stage.**"
        ),
        "",
    ]

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return output_path


def main() -> None:
    """Execute the complete Volve monthly-production audit."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "Raw workbook not found: {}".format(
                DATA_FILE
            )
        )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    _, monthly = load_monthly_data()

    qc, hour_exceptions = validate_monthly_data(
        monthly
    )

    monthly = add_engineering_metrics(
        monthly
    )

    (
        crosscheck,
        representation_differences,
    ) = crosscheck_daily_vs_monthly(
        monthly
    )

    screening = build_well_screening(
        monthly
    )

    source_sha256 = sha256sum(
        DATA_FILE
    )

    processed_path = (
        PROCESSED_DIR
        / "volve_monthly_clean.csv"
    )

    screening_path = (
        REPORT_DIR
        / "well_screening.csv"
    )

    crosscheck_path = (
        REPORT_DIR
        / "monthly_daily_crosscheck.csv"
    )

    hour_exceptions_path = (
        REPORT_DIR
        / "onstream_hour_exceptions.csv"
    )

    representation_path = (
        REPORT_DIR
        / "representation_differences.csv"
    )

    monthly.to_csv(
        processed_path,
        index=False,
    )

    screening.to_csv(
        screening_path,
        index=False,
    )

    crosscheck.to_csv(
        crosscheck_path,
        index=False,
    )

    hour_exceptions.to_csv(
        hour_exceptions_path,
        index=False,
    )

    representation_differences.to_csv(
        representation_path,
        index=False,
    )

    markdown_path = write_markdown_audit(
        source_sha256,
        monthly,
        qc,
        crosscheck,
        screening,
    )

    print(
        "\n============================================================"
    )
    print(
        "VOLVE PRODUCTION DATA - QUALITY-CONTROL AUDIT"
    )
    print(
        "============================================================"
    )

    print(
        "Source workbook : {}".format(
            DATA_FILE.name
        )
    )
    print(
        "SHA-256         : {}".format(
            source_sha256
        )
    )
    print(
        "Monthly records : {:,}".format(
            len(monthly)
        )
    )
    print(
        "Date range      : {} to {}".format(
            monthly["Date"].min().date(),
            monthly["Date"].max().date(),
        )
    )
    print(
        "Wellbores       : {}".format(
            monthly["Wellbore name"].nunique()
        )
    )

    print("\nVERIFIED MONTHLY UNITS")

    for column, expected_unit in EXPECTED_UNITS.items():
        print(
            "  {:<12} {}".format(
                column,
                expected_unit,
            )
        )

    print("\nQUALITY-CONTROL CHECKS")

    for key, value in qc.items():
        print(
            "  {:<52} {}".format(
                key,
                value,
            )
        )

    print(
        "\nMONTHLY <-> DAILY AGGREGATION CROSS-CHECK"
    )

    print(
        crosscheck.to_string(
            index=False
        )
    )

    print(
        "\nDOCUMENTED REPRESENTATION DIFFERENCES"
    )

    if representation_differences.empty:
        print("  None")
    else:
        print(
            representation_differences.to_string(
                index=False
            )
        )

    print("\nWELL SCREENING")

    display_columns = [
        "Wellbore name",
        "Role",
        "First Production",
        "Last Production",
        "First Injection",
        "Last Injection",
        "Producing Months",
        "Injection Months",
        "Oil Sm3",
        "Water Sm3",
        "Peak Oil Rate Sm3/d",
    ]

    print(
        screening[
            display_columns
        ].to_string(
            index=False
        )
    )

    print("\nDERIVED COLUMN DTYPES")

    print(
        monthly[
            [
                "Oil Rate Sm3/d",
                "Gas Rate Sm3/d",
                "Water Rate Sm3/d",
                "Water Cut",
                "GOR Sm3/Sm3",
                "Uptime Fraction",
            ]
        ].dtypes
    )

    print("\nOUTPUTS")

    for path in [
        processed_path,
        screening_path,
        crosscheck_path,
        hour_exceptions_path,
        representation_path,
        markdown_path,
    ]:
        print("  {}".format(path))

    print("\nAUDIT STATUS: PASS")


if __name__ == "__main__":
    main()
