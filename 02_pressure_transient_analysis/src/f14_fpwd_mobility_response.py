"""Mobility and pretest-response analysis for Volve 15/9-F-14 FPWD tests.

The analysis compares source-interpreted drawdown mobility with the observed
pressure response produced by the approximately consistent FPWD withdrawal
sequence.

The empirical pretest response index q_avg / delta_p is not treated as
formation mobility. It is used only as an observational response metric.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress


PROJECT_DIR = Path(__file__).resolve().parents[1]

AUDIT_FILE = (
    PROJECT_DIR
    / "report"
    / "f14_fpwd_data_audit.csv"
)

RESPONSE_FILE = (
    PROJECT_DIR
    / "report"
    / "f14_fpwd_pressure_response_summary.csv"
)

REPORT_DIR = PROJECT_DIR / "report"
FIGURE_DIR = PROJECT_DIR / "figures"

VENDOR_EXCLUDED_TESTS = {10}

# Used only to distinguish pressure responses with substantial
# drawdown amplitude from very small-amplitude responses.
RESOLVED_DRAWDOWN_BAR = 1.0


def load_data():
    """Merge metadata and observed pressure-response results."""

    audit = pd.read_csv(
        AUDIT_FILE
    )

    response = pd.read_csv(
        RESPONSE_FILE
    )

    metadata_columns = [
        "Test",
        "Drawdown Volume cc",
    ]

    df = response.merge(
        audit[metadata_columns],
        on="Test",
        how="left",
        validate="one_to_one",
    )

    df["Vendor Qualified"] = (
        ~df["Test"].isin(
            VENDOR_EXCLUDED_TESTS
        )
    )

    df["Average Withdrawal Rate cc/s"] = (
        df["Drawdown Volume cc"]
        / df["Drawdown Duration s"]
    )

    df["Pretest Response Index cc/s/bar"] = (
        df["Average Withdrawal Rate cc/s"]
        / df["Observed Drawdown bar"]
    )

    df["Resolved Drawdown"] = (
        df["Observed Drawdown bar"]
        >= RESOLVED_DRAWDOWN_BAR
    )

    return df


def regression_statistics(df):
    """Calculate log-log mobility-response regressions."""

    cases = [
        (
            "Vendor-qualified stations",
            df["Vendor Qualified"],
        ),
        (
            "Vendor-qualified, drawdown >= 1 bar",
            (
                df["Vendor Qualified"]
                & df["Resolved Drawdown"]
            ),
        ),
    ]

    rows = []

    for name, mask in cases:

        subset = df.loc[
            mask
            & (
                df[
                    "Pretest Response Index cc/s/bar"
                ]
                > 0
            )
            & (
                df[
                    "Source Mobility mD/cP"
                ]
                > 0
            )
        ].copy()

        x = np.log10(
            subset[
                "Pretest Response Index cc/s/bar"
            ]
        )

        y = np.log10(
            subset[
                "Source Mobility mD/cP"
            ]
        )

        fit = linregress(
            x,
            y,
        )

        rows.append(
            {
                "Case": name,
                "Stations": len(subset),
                "Log-Log Slope": fit.slope,
                "Log-Log Intercept": fit.intercept,
                "R2": fit.rvalue ** 2,
                "p-value": fit.pvalue,
            }
        )

    return pd.DataFrame(
        rows
    )


def create_figure(
    df,
    statistics,
):
    """Create pretest-disturbance and mobility-response diagnostics."""

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(17, 6.5),
        constrained_layout=True,
    )

    # ---------------------------------------------------------
    # A. Withdrawal disturbance
    # ---------------------------------------------------------

    ax = axes[0]

    ax.bar(
        df["Test"],
        df[
            "Average Withdrawal Rate cc/s"
        ],
        color="#0072B2",
        alpha=0.85,
    )

    ax.axhline(
        df[
            "Average Withdrawal Rate cc/s"
        ].median(),
        color="#444444",
        linestyle="--",
        linewidth=1.2,
        label="Median",
    )

    ax.set_title(
        "A. Average withdrawal rate",
        loc="left",
        fontweight="bold",
    )

    ax.set_xlabel(
        "Test"
    )

    ax.set_ylabel(
        "Average withdrawal rate (cm³/s)"
    )

    ax.set_xticks(
        df["Test"]
    )

    ax.grid(
        True,
        axis="y",
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
    )

    # ---------------------------------------------------------
    # B. Drawdown versus mobility
    # ---------------------------------------------------------

    ax = axes[1]

    qualified = df.loc[
        df["Vendor Qualified"]
    ]

    excluded = df.loc[
        ~df["Vendor Qualified"]
    ]

    ax.scatter(
        qualified[
            "Observed Drawdown bar"
        ],
        qualified[
            "Source Mobility mD/cP"
        ],
        color="#0072B2",
        s=60,
        label="Vendor-qualified",
        zorder=5,
    )

    if not excluded.empty:
        ax.scatter(
            excluded[
                "Observed Drawdown bar"
            ],
            excluded[
                "Source Mobility mD/cP"
            ],
            marker="x",
            color="#D55E00",
            linewidths=2,
            s=80,
            label="Vendor-excluded",
            zorder=6,
        )

    for _, row in df.iterrows():
        ax.annotate(
            str(
                int(
                    row["Test"]
                )
            ),
            (
                row[
                    "Observed Drawdown bar"
                ],
                row[
                    "Source Mobility mD/cP"
                ],
            ),
            xytext=(5, 3),
            textcoords="offset points",
            fontsize=8,
        )

    ax.set_xscale(
        "log"
    )

    ax.set_yscale(
        "log"
    )

    ax.set_title(
        "B. Drawdown response versus mobility",
        loc="left",
        fontweight="bold",
    )

    ax.set_xlabel(
        "Observed drawdown (bar)"
    )

    ax.set_ylabel(
        "Source mobility (mD/cP)"
    )

    ax.grid(
        True,
        which="both",
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
    )

    # ---------------------------------------------------------
    # C. Empirical response index versus mobility
    # ---------------------------------------------------------

    ax = axes[2]

    resolved = df.loc[
        df["Vendor Qualified"]
        & df["Resolved Drawdown"]
    ]

    low_amplitude = df.loc[
        df["Vendor Qualified"]
        & ~df["Resolved Drawdown"]
    ]

    ax.scatter(
        resolved[
            "Pretest Response Index cc/s/bar"
        ],
        resolved[
            "Source Mobility mD/cP"
        ],
        color="#009E73",
        s=60,
        label="Drawdown >= 1 bar",
        zorder=5,
    )

    ax.scatter(
        low_amplitude[
            "Pretest Response Index cc/s/bar"
        ],
        low_amplitude[
            "Source Mobility mD/cP"
        ],
        facecolors="none",
        edgecolors="#0072B2",
        linewidths=1.6,
        s=70,
        label="Drawdown < 1 bar",
        zorder=5,
    )

    if not excluded.empty:
        ax.scatter(
            excluded[
                "Pretest Response Index cc/s/bar"
            ],
            excluded[
                "Source Mobility mD/cP"
            ],
            marker="x",
            color="#D55E00",
            linewidths=2,
            s=80,
            zorder=6,
        )

    fit_subset = resolved.loc[
        (
            resolved[
                "Pretest Response Index cc/s/bar"
            ]
            > 0
        )
        & (
            resolved[
                "Source Mobility mD/cP"
            ]
            > 0
        )
    ]

    x = np.log10(
        fit_subset[
            "Pretest Response Index cc/s/bar"
        ]
    )

    y = np.log10(
        fit_subset[
            "Source Mobility mD/cP"
        ]
    )

    fit = linregress(
        x,
        y,
    )

    x_line = np.linspace(
        x.min(),
        x.max(),
        200,
    )

    y_line = (
        fit.intercept
        + fit.slope
        * x_line
    )

    ax.plot(
        10 ** x_line,
        10 ** y_line,
        color="#444444",
        linestyle="--",
        linewidth=1.4,
        label="Log-log fit",
    )

    for _, row in df.iterrows():
        ax.annotate(
            str(
                int(
                    row["Test"]
                )
            ),
            (
                row[
                    "Pretest Response Index cc/s/bar"
                ],
                row[
                    "Source Mobility mD/cP"
                ],
            ),
            xytext=(5, 3),
            textcoords="offset points",
            fontsize=8,
        )

    ax.set_xscale(
        "log"
    )

    ax.set_yscale(
        "log"
    )

    ax.set_title(
        "C. Empirical response index versus mobility",
        loc="left",
        fontweight="bold",
    )

    ax.set_xlabel(
        "q_avg / ΔP (cm³/s/bar)"
    )

    ax.set_ylabel(
        "Source mobility (mD/cP)"
    )

    ax.grid(
        True,
        which="both",
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
        fontsize=8,
    )

    fig.suptitle(
        "15/9-F-14 — FPWD Mobility and Pretest-Response Analysis",
        fontsize=15,
        fontweight="bold",
    )

    png_path = (
        FIGURE_DIR
        / "15_9_F_14_fpwd_mobility_response.png"
    )

    pdf_path = (
        FIGURE_DIR
        / "15_9_F_14_fpwd_mobility_response.pdf"
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

    return png_path, pdf_path


def main():
    """Execute mobility and pretest-response analysis."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    statistics = regression_statistics(
        df
    )

    response_path = (
        REPORT_DIR
        / "f14_fpwd_mobility_response.csv"
    )

    statistics_path = (
        REPORT_DIR
        / "f14_fpwd_mobility_response_statistics.csv"
    )

    df.to_csv(
        response_path,
        index=False,
    )

    statistics.to_csv(
        statistics_path,
        index=False,
    )

    png_path, pdf_path = create_figure(
        df,
        statistics,
    )

    print()
    print(
        "15/9-F-14 FPWD MOBILITY-RESPONSE ANALYSIS"
    )
    print()

    print(
        df[
            [
                "Test",
                "Drawdown Volume cc",
                "Drawdown Duration s",
                "Average Withdrawal Rate cc/s",
                "Observed Drawdown bar",
                "Pretest Response Index cc/s/bar",
                "Source Mobility mD/cP",
                "Vendor Qualified",
                "Resolved Drawdown",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "LOG-LOG RESPONSE STATISTICS"
    )
    print()

    display = statistics.copy()

    display[
        "p-value"
    ] = display[
        "p-value"
    ].apply(
        lambda value: "{:.3e}".format(
            value
        )
    )

    print(
        display.to_string(
            index=False
        )
    )

    print()
    print(
        "Outputs:"
    )

    for path in [
        response_path,
        statistics_path,
        png_path,
        pdf_path,
    ]:
        print(
            "  {}".format(
                path
            )
        )


if __name__ == "__main__":
    main()
