"""Pressure-gradient residual and robustness analysis for Volve 15/9-F-14 FPWD.

The analysis compares:
1. ordinary least-squares regression using all pressure stations;
2. ordinary least-squares regression using the vendor-qualified set
   (Test 10 excluded);
3. Theil-Sen robust regression using all stations.

Source-interpreted formation pressure is used as the primary pressure basis.
Final quartz-gauge buildup pressure is retained as an independent measurement
comparison.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import linregress, t, theilslopes


PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_DIR
    / "report"
    / "f14_fpwd_pressure_response_summary.csv"
)

REPORT_DIR = PROJECT_DIR / "report"
FIGURE_DIR = PROJECT_DIR / "figures"

BAR_TO_PSI = 14.5037738
M_TO_FT = 3.280839895
GRAVITY = 9.80665

# Schlumberger FPWD interpretation identifies Test 10 as the
# non-quality pressure measurement in this 14-station sequence.
VENDOR_EXCLUDED_TESTS = {10}


def load_data():
    """Load station-level pressure interpretation."""

    df = pd.read_csv(
        INPUT_FILE
    )

    required = [
        "Test",
        "TVD m",
        "Source Formation Pressure bar",
        "Final Buildup Pressure bar",
        "Source Mobility mD/cP",
        "Observed Drawdown bar",
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

    df["Test"] = (
        pd.to_numeric(
            df["Test"],
            errors="raise",
        )
        .astype(int)
    )

    df["Vendor Qualified"] = (
        ~df["Test"].isin(
            VENDOR_EXCLUDED_TESTS
        )
    )

    df["Final minus Source bar"] = (
        df["Final Buildup Pressure bar"]
        - df["Source Formation Pressure bar"]
    )

    return df


def ols_statistics(
    depth,
    pressure,
    name,
):
    """Calculate ordinary least-squares gradient statistics."""

    regression = linregress(
        depth,
        pressure,
    )

    n = len(depth)

    degrees_of_freedom = n - 2

    t_critical = t.ppf(
        0.975,
        degrees_of_freedom,
    )

    slope = float(
        regression.slope
    )

    slope_low = (
        slope
        - t_critical
        * regression.stderr
    )

    slope_high = (
        slope
        + t_critical
        * regression.stderr
    )

    predicted = (
        regression.intercept
        + regression.slope
        * np.asarray(depth)
    )

    residual = (
        np.asarray(pressure)
        - predicted
    )

    rmse = float(
        np.sqrt(
            np.mean(
                residual ** 2
            )
        )
    )

    return {
        "Model": name,
        "Stations": n,
        "Gradient bar/m": slope,
        "Gradient 95% CI Low bar/m": (
            slope_low
        ),
        "Gradient 95% CI High bar/m": (
            slope_high
        ),
        "Gradient bar/100m": (
            slope
            * 100.0
        ),
        "Gradient psi/ft": (
            slope
            * BAR_TO_PSI
            / M_TO_FT
        ),
        "Hydrostatic Equivalent Density kg/m3": (
            slope
            * 100000.0
            / GRAVITY
        ),
        "Intercept bar": float(
            regression.intercept
        ),
        "R2": float(
            regression.rvalue ** 2
        ),
        "p-value": float(
            regression.pvalue
        ),
        "Slope Std Error bar/m": float(
            regression.stderr
        ),
        "Residual RMSE bar": rmse,
    }


def robust_statistics(
    depth,
    pressure,
):
    """Calculate Theil-Sen robust pressure gradient."""

    result = theilslopes(
        pressure,
        depth,
        alpha=0.95,
    )

    predicted = (
        result.intercept
        + result.slope
        * np.asarray(depth)
    )

    residual = (
        np.asarray(pressure)
        - predicted
    )

    ss_res = np.sum(
        residual ** 2
    )

    ss_tot = np.sum(
        (
            np.asarray(pressure)
            - np.mean(pressure)
        ) ** 2
    )

    r2 = (
        1.0
        - ss_res / ss_tot
    )

    return {
        "Model": "Theil-Sen robust - all stations",
        "Stations": len(depth),
        "Gradient bar/m": float(
            result.slope
        ),
        "Gradient 95% CI Low bar/m": float(
            result.low_slope
        ),
        "Gradient 95% CI High bar/m": float(
            result.high_slope
        ),
        "Gradient bar/100m": float(
            result.slope
            * 100.0
        ),
        "Gradient psi/ft": float(
            result.slope
            * BAR_TO_PSI
            / M_TO_FT
        ),
        "Hydrostatic Equivalent Density kg/m3": float(
            result.slope
            * 100000.0
            / GRAVITY
        ),
        "Intercept bar": float(
            result.intercept
        ),
        "R2": float(
            r2
        ),
        "p-value": np.nan,
        "Slope Std Error bar/m": np.nan,
        "Residual RMSE bar": float(
            np.sqrt(
                np.mean(
                    residual ** 2
                )
            )
        ),
    }


def build_model_summary(df):
    """Build OLS and robust regression comparison."""

    qualified = df.loc[
        df["Vendor Qualified"]
    ].copy()

    rows = []

    rows.append(
        ols_statistics(
            df["TVD m"],
            df[
                "Source Formation Pressure bar"
            ],
            "OLS - all stations",
        )
    )

    rows.append(
        ols_statistics(
            qualified["TVD m"],
            qualified[
                "Source Formation Pressure bar"
            ],
            "OLS - vendor-qualified stations",
        )
    )

    rows.append(
        robust_statistics(
            df["TVD m"].to_numpy(),
            df[
                "Source Formation Pressure bar"
            ].to_numpy(),
        )
    )

    summary = pd.DataFrame(
        rows
    )

    return summary


def calculate_residuals(df):
    """Calculate station residuals from vendor-qualified OLS regression."""

    qualified = df.loc[
        df["Vendor Qualified"]
    ]

    regression = linregress(
        qualified["TVD m"],
        qualified[
            "Source Formation Pressure bar"
        ],
    )

    result = df.copy()

    result[
        "Predicted Pressure bar"
    ] = (
        regression.intercept
        + regression.slope
        * result["TVD m"]
    )

    result[
        "Pressure Residual bar"
    ] = (
        result[
            "Source Formation Pressure bar"
        ]
        - result[
            "Predicted Pressure bar"
        ]
    )

    result[
        "Absolute Pressure Residual bar"
    ] = (
        result[
            "Pressure Residual bar"
        ].abs()
    )

    return result


def create_figure(
    df,
    residuals,
    summary,
):
    """Create pressure-gradient robustness and residual diagnostics."""

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    qualified = df.loc[
        df["Vendor Qualified"]
    ]

    excluded = df.loc[
        ~df["Vendor Qualified"]
    ]

    depth_line = np.linspace(
        df["TVD m"].min(),
        df["TVD m"].max(),
        300,
    )

    fit_all = linregress(
        df["TVD m"],
        df[
            "Source Formation Pressure bar"
        ],
    )

    fit_qualified = linregress(
        qualified["TVD m"],
        qualified[
            "Source Formation Pressure bar"
        ],
    )

    robust = theilslopes(
        df[
            "Source Formation Pressure bar"
        ],
        df["TVD m"],
        alpha=0.95,
    )

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(17, 7),
        constrained_layout=True,
    )

    # ---------------------------------------------------------
    # A. Pressure-depth regression
    # ---------------------------------------------------------

    ax = axes[0]

    ax.scatter(
        qualified[
            "Source Formation Pressure bar"
        ],
        qualified["TVD m"],
        s=55,
        color="#0072B2",
        label="Vendor-qualified station",
        zorder=5,
    )

    if not excluded.empty:
        ax.scatter(
            excluded[
                "Source Formation Pressure bar"
            ],
            excluded["TVD m"],
            s=75,
            marker="x",
            linewidths=2.0,
            color="#D55E00",
            label="Vendor-excluded station",
            zorder=6,
        )

    ax.plot(
        (
            fit_all.intercept
            + fit_all.slope
            * depth_line
        ),
        depth_line,
        color="#7A7A7A",
        linestyle=":",
        linewidth=1.5,
        label="OLS - all stations",
    )

    ax.plot(
        (
            fit_qualified.intercept
            + fit_qualified.slope
            * depth_line
        ),
        depth_line,
        color="#0072B2",
        linewidth=1.8,
        label="OLS - vendor-qualified",
    )

    ax.plot(
        (
            robust.intercept
            + robust.slope
            * depth_line
        ),
        depth_line,
        color="#009E73",
        linestyle="--",
        linewidth=1.6,
        label="Theil-Sen robust",
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
                    "Source Formation Pressure bar"
                ],
                row["TVD m"],
            ),
            xytext=(5, -2),
            textcoords="offset points",
            fontsize=8,
        )

    ax.invert_yaxis()

    ax.set_title(
        "A. Pressure-gradient models",
        loc="left",
        fontweight="bold",
    )

    ax.set_xlabel(
        "Formation pressure (bar)"
    )

    ax.set_ylabel(
        "TVD (m)"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
        fontsize=8,
    )

    # ---------------------------------------------------------
    # B. Residuals
    # ---------------------------------------------------------

    ax = axes[1]

    ax.axvline(
        0.0,
        color="#444444",
        linewidth=1.0,
    )

    colors = np.where(
        residuals["Vendor Qualified"],
        "#0072B2",
        "#D55E00",
    )

    ax.scatter(
        residuals[
            "Pressure Residual bar"
        ],
        residuals["TVD m"],
        c=colors,
        s=55,
        zorder=5,
    )

    for _, row in residuals.iterrows():
        ax.annotate(
            str(
                int(
                    row["Test"]
                )
            ),
            (
                row[
                    "Pressure Residual bar"
                ],
                row["TVD m"],
            ),
            xytext=(5, -2),
            textcoords="offset points",
            fontsize=8,
        )

    ax.invert_yaxis()

    ax.set_title(
        "B. Residuals from vendor-qualified OLS",
        loc="left",
        fontweight="bold",
    )

    ax.set_xlabel(
        "Measured - fitted pressure (bar)"
    )

    ax.set_ylabel(
        "TVD (m)"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    # ---------------------------------------------------------
    # C. Source-versus-observed pressure agreement
    # ---------------------------------------------------------

    ax = axes[2]

    ax.axhline(
        0.0,
        color="#444444",
        linewidth=1.0,
    )

    ax.scatter(
        df["Test"],
        df[
            "Final minus Source bar"
        ],
        c=np.where(
            df["Vendor Qualified"],
            "#009E73",
            "#D55E00",
        ),
        s=55,
        zorder=5,
    )

    for _, row in df.iterrows():
        ax.annotate(
            str(
                int(
                    row["Test"]
                )
            ),
            (
                row["Test"],
                row[
                    "Final minus Source bar"
                ],
            ),
            xytext=(3, 4),
            textcoords="offset points",
            fontsize=8,
        )

    ax.set_title(
        "C. Final buildup versus source pressure",
        loc="left",
        fontweight="bold",
    )

    ax.set_xlabel(
        "Test"
    )

    ax.set_ylabel(
        "Final buildup - source pressure (bar)"
    )

    ax.set_xticks(
        df["Test"]
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.suptitle(
        "15/9-F-14 — FPWD Pressure-Gradient Robustness and Residual Analysis",
        fontsize=15,
        fontweight="bold",
    )

    png_path = (
        FIGURE_DIR
        / "15_9_F_14_fpwd_gradient_residual_analysis.png"
    )

    pdf_path = (
        FIGURE_DIR
        / "15_9_F_14_fpwd_gradient_residual_analysis.pdf"
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
    """Execute gradient robustness and residual analysis."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    summary = build_model_summary(
        df
    )

    residuals = calculate_residuals(
        df
    )

    summary_path = (
        REPORT_DIR
        / "f14_fpwd_gradient_model_comparison.csv"
    )

    residual_path = (
        REPORT_DIR
        / "f14_fpwd_gradient_residuals.csv"
    )

    summary.to_csv(
        summary_path,
        index=False,
    )

    residuals.to_csv(
        residual_path,
        index=False,
    )

    png_path, pdf_path = create_figure(
        df,
        residuals,
        summary,
    )

    display_summary = summary.copy()

    display_summary[
        "p-value"
    ] = display_summary[
        "p-value"
    ].apply(
        lambda value: (
            "{:.3e}".format(value)
            if np.isfinite(value)
            else "N/A"
        )
    )

    print()
    print(
        "15/9-F-14 PRESSURE-GRADIENT MODEL COMPARISON"
    )
    print()

    print(
        display_summary.to_string(
            index=False
        )
    )

    print()
    print(
        "STATION RESIDUALS"
    )
    print()

    print(
        residuals[
            [
                "Test",
                "TVD m",
                "Vendor Qualified",
                "Source Formation Pressure bar",
                "Predicted Pressure bar",
                "Pressure Residual bar",
                "Absolute Pressure Residual bar",
                "Final minus Source bar",
            ]
        ].to_string(
            index=False
        )
    )

    largest = residuals.loc[
        residuals[
            "Vendor Qualified"
        ],
        [
            "Test",
            "Pressure Residual bar",
        ],
    ].copy()

    largest[
        "Absolute Residual"
    ] = (
        largest[
            "Pressure Residual bar"
        ].abs()
    )

    largest = largest.sort_values(
        "Absolute Residual",
        ascending=False,
    ).iloc[0]

    print()
    print(
        "Largest absolute residual among "
        "vendor-qualified stations:"
    )

    print(
        "Test {} : {:.4f} bar".format(
            int(
                largest["Test"]
            ),
            largest[
                "Pressure Residual bar"
            ],
        )
    )

    print()
    print(
        "Outputs:"
    )

    for path in [
        summary_path,
        residual_path,
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
