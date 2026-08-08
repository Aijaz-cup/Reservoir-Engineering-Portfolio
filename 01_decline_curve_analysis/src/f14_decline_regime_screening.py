"""Decline-regime screening for Volve producer 15/9-F-14.

The analysis evaluates the selected terminal production interval using
monthly oil rate, water cut, uptime, choke position, and pressure data
before decline-curve parameters are estimated.
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress


PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_DIR
    / "report"
    / "f14_monthly_operating_summary.csv"
)

FIGURE_DIR = PROJECT_DIR / "figures"
REPORT_DIR = PROJECT_DIR / "report"

FIT_START = pd.Timestamp("2013-05-01")
FIT_END = pd.Timestamp("2016-03-01")

LATE_OPERATION_START = pd.Timestamp("2016-04-01")


def load_data() -> pd.DataFrame:
    """Read the monthly F-14 operating summary."""

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["Month"],
    )

    required = [
        "Month",
        "Uptime Fraction",
        "Oil Rate Sm3/d",
        "Water Rate Sm3/d",
        "Water Cut",
        "GOR Sm3/Sm3",
        "Avg Choke Size",
        "Avg WHP",
        "Avg Downhole Pressure",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: {}".format(
                missing
            )
        )

    return (
        df.sort_values("Month")
        .reset_index(drop=True)
    )


def selected_window(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Return the selected decline-regime interval."""

    window = df.loc[
        (df["Month"] >= FIT_START)
        & (df["Month"] <= FIT_END)
        & df["Oil Rate Sm3/d"].notna()
    ].copy()

    if window.empty:
        raise ValueError(
            "Selected decline interval contains no data."
        )

    return window


def calculate_metrics(
    window: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate reproducible screening metrics."""

    elapsed_months = (
        (
            window["Month"].dt.year
            - FIT_START.year
        )
        * 12
        + (
            window["Month"].dt.month
            - FIT_START.month
        )
    ).astype(float)

    log_oil_rate = np.log(
        window["Oil Rate Sm3/d"].to_numpy(
            dtype=float
        )
    )

    regression = linregress(
        elapsed_months,
        log_oil_rate,
    )

    oil = (
        window["Oil Rate Sm3/d"]
        .to_numpy(dtype=float)
    )

    monthly_decline_fraction = float(
        np.mean(
            np.diff(oil) < 0
        )
    )

    first = window.iloc[0]
    last = window.iloc[-1]

    metrics = {
        "Wellbore": "15/9-F-14",
        "Fit Start": FIT_START.date(),
        "Fit End": FIT_END.date(),
        "Months": int(len(window)),
        "Initial Oil Rate Sm3/d": float(
            first["Oil Rate Sm3/d"]
        ),
        "Final Oil Rate Sm3/d": float(
            last["Oil Rate Sm3/d"]
        ),
        "Oil Rate Reduction Fraction": float(
            1.0
            - last["Oil Rate Sm3/d"]
            / first["Oil Rate Sm3/d"]
        ),
        "Initial Water Cut": float(
            first["Water Cut"]
        ),
        "Final Water Cut": float(
            last["Water Cut"]
        ),
        "Median Uptime Fraction": float(
            window["Uptime Fraction"].median()
        ),
        "Minimum Uptime Fraction": float(
            window["Uptime Fraction"].min()
        ),
        "Median Choke Size": float(
            window["Avg Choke Size"].median()
        ),
        "Minimum Choke Size": float(
            window["Avg Choke Size"].min()
        ),
        "Maximum Choke Size": float(
            window["Avg Choke Size"].max()
        ),
        "Declining Month Fraction": (
            monthly_decline_fraction
        ),
        "Log-Rate Linear R2": float(
            regression.rvalue ** 2
        ),
    }

    result = pd.DataFrame(
        [metrics]
    )

    numeric_columns = result.select_dtypes(
        include=[np.number]
    ).columns

    result[numeric_columns] = (
        result[numeric_columns]
        .round(4)
    )

    return result


def format_date_axis(ax) -> None:
    """Apply consistent yearly date formatting."""

    ax.xaxis.set_major_locator(
        mdates.YearLocator()
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )

    ax.xaxis.set_minor_locator(
        mdates.MonthLocator(interval=6)
    )

    ax.grid(
        True,
        alpha=0.25,
    )


def shade_selected_interval(ax) -> None:
    """Show the selected DCA interval."""

    ax.axvspan(
        FIT_START,
        FIT_END,
        color="#D9EAF7",
        alpha=0.45,
        label="Selected decline interval",
    )

    ax.axvline(
        FIT_START,
        color="#005B96",
        linestyle="--",
        linewidth=1.3,
    )

    ax.axvline(
        FIT_END,
        color="#005B96",
        linestyle="--",
        linewidth=1.3,
    )


def create_diagnostic_figure(
    df: pd.DataFrame,
) -> None:
    """Create the F-14 decline-regime diagnostic figure."""

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plotting = df.loc[
        (
            df["Month"]
            >= pd.Timestamp("2012-01-01")
        )
        & (
            df["Month"]
            <= pd.Timestamp("2016-07-01")
        )
    ].copy()

    fig, axes = plt.subplots(
        4,
        1,
        figsize=(12, 12),
        sharex=True,
        constrained_layout=True,
    )

    fig.suptitle(
        "15/9-F-14 — Decline-Regime Screening",
        fontsize=16,
        fontweight="bold",
    )

    # ---------------------------------------------------------
    # A. Oil rate
    # ---------------------------------------------------------

    ax = axes[0]

    shade_selected_interval(ax)

    ax.plot(
        plotting["Month"],
        plotting["Oil Rate Sm3/d"],
        color="#D55E00",
        linewidth=2.0,
        label="Oil rate",
    )

    ax.set_ylabel(
        "Oil rate\n(Sm³/d)"
    )

    ax.set_title(
        "A. Producing-day oil rate",
        loc="left",
        fontweight="bold",
    )

    ax.set_ylim(
        bottom=0
    )

    ax.legend(
        frameon=False,
        loc="upper right",
    )

    format_date_axis(ax)

    # ---------------------------------------------------------
    # B. Uptime and choke
    # ---------------------------------------------------------

    ax = axes[1]

    shade_selected_interval(ax)

    ax.plot(
        plotting["Month"],
        plotting["Uptime Fraction"] * 100.0,
        color="#555555",
        linewidth=1.8,
        label="Uptime",
    )

    ax.axhline(
        100.0,
        color="#999999",
        linestyle="--",
        linewidth=1.0,
    )

    ax.set_ylabel(
        "Uptime (%)"
    )

    ax.set_ylim(
        0,
        105,
    )

    choke_ax = ax.twinx()

    choke_ax.plot(
        plotting["Month"],
        plotting["Avg Choke Size"],
        color="#009E73",
        linewidth=1.8,
        label="Choke",
    )

    choke_ax.set_ylabel(
        "Average choke (%)",
        color="#009E73",
    )

    choke_ax.set_ylim(
        0,
        105,
    )

    ax.set_title(
        "B. Operating uptime and choke position",
        loc="left",
        fontweight="bold",
    )

    format_date_axis(ax)

    # ---------------------------------------------------------
    # C. Pressure
    # ---------------------------------------------------------

    ax = axes[2]

    shade_selected_interval(ax)

    ax.plot(
        plotting["Month"],
        plotting["Avg Downhole Pressure"],
        color="#0072B2",
        linewidth=1.8,
        label="Downhole pressure",
    )

    ax.set_ylabel(
        "Downhole pressure"
    )

    whp_ax = ax.twinx()

    whp_ax.plot(
        plotting["Month"],
        plotting["Avg WHP"],
        color="#CC79A7",
        linewidth=1.8,
        label="WHP",
    )

    whp_ax.set_ylabel(
        "Wellhead pressure",
        color="#CC79A7",
    )

    ax.set_title(
        "C. Flowing pressure indicators",
        loc="left",
        fontweight="bold",
    )

    format_date_axis(ax)

    # ---------------------------------------------------------
    # D. Water cut
    # ---------------------------------------------------------

    ax = axes[3]

    shade_selected_interval(ax)

    ax.plot(
        plotting["Month"],
        plotting["Water Cut"] * 100.0,
        color="#0072B2",
        linewidth=2.0,
    )

    ax.set_ylabel(
        "Water cut (%)"
    )

    ax.set_xlabel(
        "Date"
    )

    ax.set_ylim(
        50,
        100,
    )

    ax.set_title(
        "D. Produced-water evolution",
        loc="left",
        fontweight="bold",
    )

    format_date_axis(ax)

    png_path = (
        FIGURE_DIR
        / "15_9_F_14_decline_regime_screening.png"
    )

    pdf_path = (
        FIGURE_DIR
        / "15_9_F_14_decline_regime_screening.pdf"
    )

    fig.savefig(
        png_path,
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        pdf_path,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(
        "Saved: {}".format(
            png_path
        )
    )

    print(
        "Saved: {}".format(
            pdf_path
        )
    )


def main() -> None:
    """Execute decline-regime screening."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    window = selected_window(
        df
    )

    metrics = calculate_metrics(
        window
    )

    output_path = (
        REPORT_DIR
        / "f14_decline_window_metrics.csv"
    )

    metrics.to_csv(
        output_path,
        index=False,
    )

    create_diagnostic_figure(
        df
    )

    print(
        "\n=============================================="
    )

    print(
        "15/9-F-14 DECLINE-REGIME SCREENING"
    )

    print(
        "=============================================="
    )

    print()

    print(
        metrics.to_string(
            index=False
        )
    )

    print()

    print(
        "Output: {}".format(
            output_path
        )
    )


if __name__ == "__main__":
    main()
