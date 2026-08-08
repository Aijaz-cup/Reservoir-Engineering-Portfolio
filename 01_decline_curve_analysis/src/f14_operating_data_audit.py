"""Operational-data audit for Volve well 15/9-F-14.

The script evaluates the availability of daily operating measurements and
constructs monthly operating summaries for decline-regime screening.
"""

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "Volve production data.xlsx"
)

REPORT_DIR = PROJECT_DIR / "report"

DAILY_SHEET = "Daily Production Data"

WELL_NAME = "15/9-F-14"
NPD_CODE = 5351


DAILY_NUMERIC_COLUMNS = [
    "ON_STREAM_HRS",
    "AVG_DOWNHOLE_PRESSURE",
    "AVG_DOWNHOLE_TEMPERATURE",
    "AVG_DP_TUBING",
    "AVG_ANNULUS_PRESS",
    "AVG_CHOKE_SIZE_P",
    "AVG_WHP_P",
    "AVG_WHT_P",
    "DP_CHOKE_SIZE",
    "BORE_OIL_VOL",
    "BORE_GAS_VOL",
    "BORE_WAT_VOL",
]


def weighted_mean(
    values: pd.Series,
    weights: pd.Series,
) -> float:
    """Return an on-stream-hours weighted mean."""

    valid = (
        values.notna()
        & weights.notna()
        & (weights > 0)
    )

    if not valid.any():
        return np.nan

    return float(
        np.average(
            values.loc[valid],
            weights=weights.loc[valid],
        )
    )


def load_daily_data() -> pd.DataFrame:
    """Read and prepare the F-14 daily production history."""

    df = pd.read_excel(
        DATA_FILE,
        sheet_name=DAILY_SHEET,
        engine="openpyxl",
    )

    required_columns = [
        "DATEPRD",
        "NPD_WELL_BORE_CODE",
        *DAILY_NUMERIC_COLUMNS,
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required daily columns: {}".format(
                missing
            )
        )

    df["DATEPRD"] = pd.to_datetime(
        df["DATEPRD"],
        errors="raise",
    )

    df["NPD_WELL_BORE_CODE"] = pd.to_numeric(
        df["NPD_WELL_BORE_CODE"],
        errors="raise",
    )

    df = (
        df.loc[
            df["NPD_WELL_BORE_CODE"] == NPD_CODE
        ]
        .copy()
        .sort_values("DATEPRD")
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError(
            "No daily records found for {}".format(
                WELL_NAME
            )
        )

    for column in DAILY_NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df["Month"] = (
        df["DATEPRD"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    df["Producing"] = (
        df["ON_STREAM_HRS"].fillna(0.0) > 0
    )

    return df


def build_coverage_table(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize measurement coverage during producing days."""

    producing = df.loc[
        df["Producing"]
    ]

    rows = []

    for column in DAILY_NUMERIC_COLUMNS:

        valid = producing[column].notna()

        rows.append(
            {
                "Variable": column,
                "Producing Days": int(
                    len(producing)
                ),
                "Available Values": int(
                    valid.sum()
                ),
                "Coverage Fraction": (
                    float(valid.mean())
                    if len(producing)
                    else np.nan
                ),
                "First Available Date": (
                    producing.loc[
                        valid,
                        "DATEPRD",
                    ].min()
                    if valid.any()
                    else pd.NaT
                ),
                "Last Available Date": (
                    producing.loc[
                        valid,
                        "DATEPRD",
                    ].max()
                    if valid.any()
                    else pd.NaT
                ),
            }
        )

    result = pd.DataFrame(rows)

    result["Coverage Fraction"] = (
        result["Coverage Fraction"].round(4)
    )

    return result


def build_monthly_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate daily operating data to monthly surveillance metrics."""

    rows = []

    for month, group in df.groupby(
        "Month",
        sort=True,
    ):

        onstream = (
            group["ON_STREAM_HRS"]
            .fillna(0.0)
        )

        oil = (
            group["BORE_OIL_VOL"]
            .fillna(0.0)
            .sum()
        )

        gas = (
            group["BORE_GAS_VOL"]
            .fillna(0.0)
            .sum()
        )

        water = (
            group["BORE_WAT_VOL"]
            .fillna(0.0)
            .sum()
        )

        total_hours = float(
            onstream.sum()
        )

        calendar_hours = float(
            month.days_in_month * 24
        )

        producing_days_equivalent = (
            total_hours / 24.0
        )

        oil_rate = (
            oil / producing_days_equivalent
            if producing_days_equivalent > 0
            else np.nan
        )

        water_rate = (
            water / producing_days_equivalent
            if producing_days_equivalent > 0
            else np.nan
        )

        liquid = oil + water

        water_cut = (
            water / liquid
            if liquid > 0
            else np.nan
        )

        gor = (
            gas / oil
            if oil > 0
            else np.nan
        )

        rows.append(
            {
                "Month": month,
                "On Stream Hours": total_hours,
                "Uptime Fraction": (
                    total_hours
                    / calendar_hours
                ),
                "Oil Sm3": oil,
                "Water Sm3": water,
                "Gas Sm3": gas,
                "Oil Rate Sm3/d": oil_rate,
                "Water Rate Sm3/d": water_rate,
                "Water Cut": water_cut,
                "GOR Sm3/Sm3": gor,
                "Avg Choke Size": weighted_mean(
                    group[
                        "AVG_CHOKE_SIZE_P"
                    ],
                    onstream,
                ),
                "Avg WHP": weighted_mean(
                    group[
                        "AVG_WHP_P"
                    ],
                    onstream,
                ),
                "Avg Downhole Pressure": weighted_mean(
                    group[
                        "AVG_DOWNHOLE_PRESSURE"
                    ],
                    onstream,
                ),
                "Avg DP Tubing": weighted_mean(
                    group[
                        "AVG_DP_TUBING"
                    ],
                    onstream,
                ),
            }
        )

    monthly = pd.DataFrame(rows)

    numeric_columns = [
        column
        for column in monthly.columns
        if column != "Month"
    ]

    monthly[numeric_columns] = (
        monthly[numeric_columns]
        .round(4)
    )

    return monthly


def main() -> None:
    """Run the F-14 operating-data audit."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    daily = load_daily_data()

    coverage = build_coverage_table(
        daily
    )

    monthly = build_monthly_summary(
        daily
    )

    coverage_path = (
        REPORT_DIR
        / "f14_operating_data_coverage.csv"
    )

    monthly_path = (
        REPORT_DIR
        / "f14_monthly_operating_summary.csv"
    )

    coverage.to_csv(
        coverage_path,
        index=False,
    )

    monthly.to_csv(
        monthly_path,
        index=False,
    )

    print(
        "\n============================================================"
    )
    print(
        "15/9-F-14 OPERATING-DATA AUDIT"
    )
    print(
        "============================================================"
    )

    print(
        "\nDAILY RECORDS"
    )

    print(
        "First record : {}".format(
            daily["DATEPRD"].min().date()
        )
    )

    print(
        "Last record  : {}".format(
            daily["DATEPRD"].max().date()
        )
    )

    print(
        "Records      : {:,}".format(
            len(daily)
        )
    )

    print(
        "Producing days recorded : {:,}".format(
            int(daily["Producing"].sum())
        )
    )

    print(
        "\nOPERATING-DATA COVERAGE"
    )

    print(
        coverage.to_string(
            index=False
        )
    )

    print(
        "\nMONTHLY SUMMARY - LAST 15 RECORDS"
    )

    print(
        monthly.tail(15).to_string(
            index=False
        )
    )

    print(
        "\nOUTPUTS"
    )

    print(
        "  {}".format(
            coverage_path
        )
    )

    print(
        "  {}".format(
            monthly_path
        )
    )


if __name__ == "__main__":
    main()
