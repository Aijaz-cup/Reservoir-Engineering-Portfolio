"""Production-surveillance screening for Volve DCA candidate wells.

This module evaluates selected producer histories before any decline-curve
fitting is performed. It creates consistent well-level surveillance figures
and objective screening metrics for rate behavior, produced-water evolution,
gas-oil ratio, uptime, and production-history length.

No DCA fitting interval is selected automatically in this stage. Selection of
a decline regime requires engineering interpretation of the surveillance
results.
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from monthly_data_audit import (
    add_engineering_metrics,
    load_monthly_data,
)


# ---------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

FIGURE_DIR = PROJECT_DIR / "figures"
REPORT_DIR = PROJECT_DIR / "report"

CANDIDATE_WELLS = [
    "15/9-F-12",
    "15/9-F-14",
    "15/9-F-11",
]

WELL_COLORS = {
    "15/9-F-12": "#005B96",
    "15/9-F-14": "#D55E00",
    "15/9-F-11": "#009E73",
}


# ---------------------------------------------------------------------
# Plot styling
# ---------------------------------------------------------------------

def configure_plot_style() -> None:
    """Apply a clean, consistent style suitable for technical reporting."""

    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#333333",
            "axes.labelcolor": "#222222",
            "axes.titleweight": "bold",
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "font.family": "DejaVu Sans",
            "grid.color": "#B0B0B0",
            "grid.alpha": 0.28,
            "grid.linewidth": 0.7,
            "lines.linewidth": 1.8,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
        }
    )


# ---------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------

def load_surveillance_data() -> pd.DataFrame:
    """Load the audited monthly dataset and calculate surveillance metrics."""

    _, monthly = load_monthly_data()

    monthly = add_engineering_metrics(
        monthly
    )

    monthly = monthly.copy()

    monthly["Liquid Rate Sm3/d"] = (
        monthly[
            [
                "Oil Rate Sm3/d",
                "Water Rate Sm3/d",
            ]
        ]
        .sum(
            axis=1,
            min_count=1,
        )
    )

    return monthly


def producer_history(
    data: pd.DataFrame,
    well: str,
) -> pd.DataFrame:
    """Return months with positive production for screening calculations."""

    well_data = (
        data.loc[
            data["Wellbore name"] == well
        ]
        .copy()
        .sort_values("Date")
    )

    if well_data.empty:
        raise ValueError(
            "Well '{}' was not found in the dataset.".format(
                well
            )
        )

    producing = well_data.loc[
        well_data["Is Producer"]
    ].copy()

    if producing.empty:
        raise ValueError(
            "Well '{}' has no producing months.".format(
                well
            )
        )

    return producing


def surveillance_history(
    data: pd.DataFrame,
    well: str,
) -> pd.DataFrame:
    """Return the complete monthly record between first and last production."""

    well_data = (
        data.loc[
            data["Wellbore name"] == well
        ]
        .copy()
        .sort_values("Date")
    )

    producing = well_data.loc[
        well_data["Is Producer"]
    ]

    if producing.empty:
        raise ValueError(
            "Well '{}' has no producing months.".format(
                well
            )
        )

    first_production = producing["Date"].min()
    last_production = producing["Date"].max()

    return (
        well_data.loc[
            (well_data["Date"] >= first_production)
            & (well_data["Date"] <= last_production)
        ]
        .copy()
        .sort_values("Date")
    )


# ---------------------------------------------------------------------
# Screening metrics
# ---------------------------------------------------------------------

def build_candidate_screening(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate objective surveillance metrics for candidate producers."""

    rows = []

    for well in CANDIDATE_WELLS:

        history = producer_history(
            data,
            well,
        )

        positive_oil = history.loc[
            history["Oil"].fillna(0.0) > 0
        ].copy()

        peak_index = (
            positive_oil[
                "Oil Rate Sm3/d"
            ]
            .idxmax()
        )

        peak_row = positive_oil.loc[
            peak_index
        ]

        last_row = positive_oil.iloc[-1]

        first_row = positive_oil.iloc[0]

        post_peak = positive_oil.loc[
            positive_oil["Date"]
            >= peak_row["Date"]
        ]

        rows.append(
            {
                "Wellbore": well,
                "First Production": (
                    positive_oil["Date"]
                    .min()
                ),
                "Last Production": (
                    positive_oil["Date"]
                    .max()
                ),
                "Producing Months": int(
                    len(positive_oil)
                ),
                "Post-Peak Producing Months": int(
                    len(post_peak)
                ),
                "Peak Oil Rate Sm3/d": float(
                    peak_row[
                        "Oil Rate Sm3/d"
                    ]
                ),
                "Peak Oil Rate Date": (
                    peak_row["Date"]
                ),
                "First Oil Rate Sm3/d": float(
                    first_row[
                        "Oil Rate Sm3/d"
                    ]
                ),
                "Last Oil Rate Sm3/d": float(
                    last_row[
                        "Oil Rate Sm3/d"
                    ]
                ),
                "Last-to-Peak Rate Fraction": float(
                    last_row[
                        "Oil Rate Sm3/d"
                    ]
                    / peak_row[
                        "Oil Rate Sm3/d"
                    ]
                ),
                "Cumulative Oil Sm3": float(
                    positive_oil[
                        "Oil"
                    ]
                    .fillna(0.0)
                    .sum()
                ),
                "Cumulative Water Sm3": float(
                    positive_oil[
                        "Water"
                    ]
                    .fillna(0.0)
                    .sum()
                ),
                "Median Uptime Fraction": float(
                    positive_oil[
                        "Uptime Fraction"
                    ]
                    .median()
                ),
                "Minimum Uptime Fraction": float(
                    positive_oil[
                        "Uptime Fraction"
                    ]
                    .min()
                ),
                "Initial Water Cut": float(
                    first_row[
                        "Water Cut"
                    ]
                ),
                "Final Water Cut": float(
                    last_row[
                        "Water Cut"
                    ]
                ),
                "Maximum Water Cut": float(
                    positive_oil[
                        "Water Cut"
                    ]
                    .max()
                ),
                "Initial GOR Sm3/Sm3": float(
                    first_row[
                        "GOR Sm3/Sm3"
                    ]
                ),
                "Final GOR Sm3/Sm3": float(
                    last_row[
                        "GOR Sm3/Sm3"
                    ]
                ),
            }
        )

    screening = pd.DataFrame(
        rows
    )

    numeric_rounding = {
        "Peak Oil Rate Sm3/d": 2,
        "First Oil Rate Sm3/d": 2,
        "Last Oil Rate Sm3/d": 2,
        "Last-to-Peak Rate Fraction": 4,
        "Cumulative Oil Sm3": 2,
        "Cumulative Water Sm3": 2,
        "Median Uptime Fraction": 4,
        "Minimum Uptime Fraction": 4,
        "Initial Water Cut": 4,
        "Final Water Cut": 4,
        "Maximum Water Cut": 4,
        "Initial GOR Sm3/Sm3": 2,
        "Final GOR Sm3/Sm3": 2,
    }

    return screening.round(
        numeric_rounding
    )


# ---------------------------------------------------------------------
# Figure utilities
# ---------------------------------------------------------------------

def format_date_axis(ax) -> None:
    """Apply a clean year-based date axis."""

    ax.xaxis.set_major_locator(
        mdates.YearLocator()
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )

    ax.xaxis.set_minor_locator(
        mdates.MonthLocator(
            interval=6
        )
    )

    ax.grid(
        True,
        which="major",
    )


def save_figure(
    fig,
    filename_stem: str,
) -> None:
    """Save both high-resolution PNG and vector PDF outputs."""

    png_path = (
        FIGURE_DIR
        / "{}.png".format(
            filename_stem
        )
    )

    pdf_path = (
        FIGURE_DIR
        / "{}.pdf".format(
            filename_stem
        )
    )

    fig.savefig(
        png_path,
        dpi=300,
    )

    fig.savefig(
        pdf_path,
    )

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


# ---------------------------------------------------------------------
# Individual-well surveillance
# ---------------------------------------------------------------------

def plot_well_surveillance(
    data: pd.DataFrame,
    well: str,
) -> None:
    """Create a four-panel production-surveillance figure for one producer."""

    history = surveillance_history(
        data,
        well,
    )

    color = WELL_COLORS[well]

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(12.0, 7.6),
        constrained_layout=True,
    )

    fig.suptitle(
        "{} — Production Surveillance".format(
            well
        ),
        fontsize=15,
        fontweight="bold",
    )

    # -------------------------------------------------------------
    # Panel A — Oil and water rates
    # -------------------------------------------------------------

    ax = axes[0, 0]

    ax.plot(
        history["Date"],
        history["Oil Rate Sm3/d"],
        color=color,
        label="Oil rate",
    )

    ax.plot(
        history["Date"],
        history["Water Rate Sm3/d"],
        color="#56B4E9",
        linestyle="--",
        label="Water rate",
    )

    ax.set_title(
        "A. Producing-day rates"
    )

    ax.set_ylabel(
        "Rate (Sm³/d)"
    )

    ax.set_ylim(
        bottom=0
    )

    ax.legend(
        frameon=False
    )

    format_date_axis(ax)

    # -------------------------------------------------------------
    # Panel B — Water cut
    # -------------------------------------------------------------

    ax = axes[0, 1]

    ax.plot(
        history["Date"],
        history["Water Cut"] * 100.0,
        color="#0072B2",
    )

    ax.set_title(
        "B. Produced-water evolution"
    )

    ax.set_ylabel(
        "Water cut (%)"
    )

    ax.set_ylim(
        0,
        100,
    )

    format_date_axis(ax)

    # -------------------------------------------------------------
    # Panel C — GOR
    # -------------------------------------------------------------

    ax = axes[1, 0]

    ax.plot(
        history["Date"],
        history["GOR Sm3/Sm3"],
        color="#CC79A7",
    )

    ax.set_title(
        "C. Producing gas-oil ratio"
    )

    ax.set_ylabel(
        "GOR (Sm³/Sm³)"
    )

    ax.set_xlabel(
        "Date"
    )

    gor = history["GOR Sm3/Sm3"].dropna()

    if not gor.empty:
        padding = max(
            5.0,
            0.10 * float(gor.max() - gor.min()),
        )

        ax.set_ylim(
            max(0.0, float(gor.min()) - padding),
            float(gor.max()) + padding,
        )

    format_date_axis(ax)

    # -------------------------------------------------------------
    # Panel D — Uptime
    # -------------------------------------------------------------

    ax = axes[1, 1]

    ax.plot(
        history["Date"],
        history["Uptime Fraction"] * 100.0,
        color="#555555",
    )

    ax.axhline(
        100.0,
        color="#999999",
        linewidth=1.0,
        linestyle="--",
        label="Nominal full-month uptime",
    )

    ax.set_title(
        "D. Monthly uptime"
    )

    ax.set_ylabel(
        "Uptime (%)"
    )

    ax.set_xlabel(
        "Date"
    )

    upper_limit = max(
        105.0,
        float(
            history[
                "Uptime Fraction"
            ].max()
            * 100.0
            * 1.03
        ),
    )

    ax.set_ylim(
        0,
        upper_limit,
    )

    ax.legend(
        frameon=False,
        loc="lower right",
    )

    format_date_axis(ax)

    safe_name = (
        well.replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )

    save_figure(
        fig,
        "{}_well_surveillance".format(
            safe_name
        ),
    )

    plt.close(
        fig
    )


# ---------------------------------------------------------------------
# Candidate comparison figure
# ---------------------------------------------------------------------

def plot_candidate_comparison(
    data: pd.DataFrame,
) -> None:
    """Compare oil-rate histories for the three candidate producers."""

    fig, ax = plt.subplots(
        figsize=(11.5, 6.3),
        constrained_layout=True,
    )

    for well in CANDIDATE_WELLS:

        history = surveillance_history(
            data,
            well,
        )

        ax.plot(
            history["Date"],
            history["Oil Rate Sm3/d"],
            label=well,
            color=WELL_COLORS[well],
        )

    ax.set_title(
        "Volve DCA Candidate Producers — Oil-Rate History",
        fontsize=14,
        fontweight="bold",
    )

    ax.set_ylabel(
        "Producing-day oil rate (Sm³/d)"
    )

    ax.set_xlabel(
        "Date"
    )

    ax.set_ylim(
        bottom=0
    )

    ax.legend(
        title="Wellbore",
        frameon=False,
    )

    format_date_axis(
        ax
    )

    save_figure(
        fig,
        "dca_candidate_oil_rate_comparison",
    )

    plt.close(
        fig
    )


# ---------------------------------------------------------------------
# Markdown summary
# ---------------------------------------------------------------------

def write_surveillance_report(
    screening: pd.DataFrame,
) -> Path:
    """Write the technical well-surveillance summary."""

    output_path = (
        REPORT_DIR
        / "WELL_SURVEILLANCE.md"
    )

    lines = [
        "# Volve Well Production Surveillance",
        "",
        "## Candidate Producers",
        "",
        (
            "Production histories were reviewed for `15/9-F-12`, "
            "`15/9-F-14`, and `15/9-F-11` using monthly "
            "producing-day rates and production-surveillance indicators."
        ),
        "",
        "## Surveillance Variables",
        "",
        "- Producing-day oil rate",
        "- Producing-day water rate",
        "- Water cut",
        "- Gas-oil ratio",
        "- Monthly uptime",
        "- Peak oil rate",
        "- Production-history duration",
        "",
        "## Engineering Observations",
        "",
        (
            "- `15/9-F-14` exhibits the most sustained long-term oil-rate "
            "decline of the three candidates. Its water cut increases "
            "progressively through field life while GOR remains comparatively "
            "stable."
        ),
        (
            "- `15/9-F-12` has a long production history but exhibits a "
            "pronounced production-regime discontinuity around 2015, with "
            "simultaneous changes in oil rate, water rate, and water cut. "
            "A single decline model should not be fitted across this "
            "discontinuity without further operational review."
        ),
        (
            "- `15/9-F-11` has a shorter history and reaches its peak oil "
            "rate relatively late in the record, leaving a substantially "
            "shorter post-peak decline interval."
        ),
        "",
        "## DCA Suitability",
        "",
        (
            "`15/9-F-14` is retained as the primary candidate for detailed "
            "decline-regime screening. `15/9-F-12` and `15/9-F-11` are "
            "retained as comparison cases."
        ),
        "",
        "The exact fitting interval is not assumed from the peak-rate date. "
        "Monthly uptime and operating-condition changes must be screened "
        "before decline parameters are estimated.",
        "",
    ]

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return output_path


# ---------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------

def main() -> None:
    """Run Stage 02 candidate well surveillance."""

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    configure_plot_style()

    data = load_surveillance_data()

    screening = build_candidate_screening(
        data
    )

    screening_path = (
        REPORT_DIR
        / "dca_candidate_screening.csv"
    )

    screening.to_csv(
        screening_path,
        index=False,
    )

    for well in CANDIDATE_WELLS:
        plot_well_surveillance(
            data,
            well,
        )

    plot_candidate_comparison(
        data
    )

    markdown_path = write_surveillance_report(
        screening
    )

    print(
        "\n============================================================"
    )
    print(
        "VOLVE WELL SURVEILLANCE - DCA CANDIDATE SCREENING"
    )
    print(
        "============================================================"
    )

    print(
        "\nCANDIDATE SCREENING"
    )

    print(
        screening.to_string(
            index=False
        )
    )

    print(
        "\nOUTPUTS"
    )

    print(
        "  {}".format(
            screening_path
        )
    )

    print(
        "  {}".format(
            markdown_path
        )
    )

    print(
        "  Figures: {}".format(
            FIGURE_DIR
        )
    )

    print(
        "\nSURVEILLANCE STATUS: PASS"
    )


if __name__ == "__main__":
    main()
