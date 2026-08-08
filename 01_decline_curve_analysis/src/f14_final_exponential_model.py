"""Final exponential decline model for Volve producer 15/9-F-14.

The exponential model is fitted to the selected May 2013 through March 2016
decline interval. Parameter uncertainty, residual statistics, and technical
rate-threshold projections are calculated explicitly.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import t as student_t


PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_DIR
    / "report"
    / "f14_monthly_operating_summary.csv"
)

REPORT_DIR = PROJECT_DIR / "report"
FIGURE_DIR = PROJECT_DIR / "figures"

FIT_START = pd.Timestamp("2013-05-01")
FIT_END = pd.Timestamp("2016-03-01")

FORECAST_MONTHS = 60

RATE_THRESHOLDS = [
    100.0,
    75.0,
    50.0,
    25.0,
]


def exponential(t, qi, d):
    """Continuous exponential decline model."""

    return qi * np.exp(
        -d * t
    )


def load_data():
    """Load the selected F-14 decline interval."""

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["Month"],
    )

    df = (
        df.loc[
            (df["Month"] >= FIT_START)
            & (df["Month"] <= FIT_END)
            & df["Oil Rate Sm3/d"].notna()
        ]
        .copy()
        .sort_values("Month")
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError(
            "Selected F-14 decline interval is empty."
        )

    df["t_months"] = np.arange(
        len(df),
        dtype=float,
    )

    return df


def fit_final_model(df):
    """Fit the exponential model to all selected observations."""

    t = df["t_months"].to_numpy(
        dtype=float
    )

    q = df["Oil Rate Sm3/d"].to_numpy(
        dtype=float
    )

    slope = np.polyfit(
        t,
        np.log(q),
        1,
    )[0]

    initial_d = max(
        -float(slope),
        1.0e-6,
    )

    parameters, covariance = curve_fit(
        exponential,
        t,
        q,
        p0=[
            float(q[0]),
            initial_d,
        ],
        bounds=(
            [0.0, 0.0],
            [np.inf, 5.0],
        ),
        maxfev=50000,
    )

    qi = float(
        parameters[0]
    )

    d = float(
        parameters[1]
    )

    prediction = exponential(
        t,
        qi,
        d,
    )

    residuals = (
        q - prediction
    )

    n = len(q)
    k = len(parameters)

    dof = (
        n - k
    )

    rss = float(
        np.sum(
            residuals ** 2
        )
    )

    residual_variance = (
        rss / dof
    )

    rmse = float(
        np.sqrt(
            np.mean(
                residuals ** 2
            )
        )
    )

    mae = float(
        np.mean(
            np.abs(residuals)
        )
    )

    mape = float(
        np.mean(
            np.abs(
                residuals / q
            )
        )
        * 100.0
    )

    ss_tot = float(
        np.sum(
            (
                q - np.mean(q)
            )
            ** 2
        )
    )

    r2 = float(
        1.0
        - rss / ss_tot
    )

    standard_errors = np.sqrt(
        np.diag(
            covariance
        )
    )

    critical_t = float(
        student_t.ppf(
            0.975,
            dof,
        )
    )

    qi_se = float(
        standard_errors[0]
    )

    d_se = float(
        standard_errors[1]
    )

    qi_ci_low = (
        qi
        - critical_t * qi_se
    )

    qi_ci_high = (
        qi
        + critical_t * qi_se
    )

    d_ci_low = max(
        0.0,
        d
        - critical_t * d_se
    )

    d_ci_high = (
        d
        + critical_t * d_se
    )

    return {
        "qi": qi,
        "d": d,
        "qi_se": qi_se,
        "d_se": d_se,
        "qi_ci_low": qi_ci_low,
        "qi_ci_high": qi_ci_high,
        "d_ci_low": d_ci_low,
        "d_ci_high": d_ci_high,
        "rmse": rmse,
        "mae": mae,
        "mape": mape,
        "r2": r2,
        "residual_variance": residual_variance,
        "prediction": prediction,
        "residuals": residuals,
    }


def build_model_summary(
    df,
    result,
):
    """Create final model-parameter summary."""

    d = result["d"]

    effective_monthly_decline = (
        1.0
        - np.exp(-d)
    )

    effective_annual_decline = (
        1.0
        - np.exp(
            -12.0 * d
        )
    )

    half_life = (
        np.log(2.0)
        / d
    )

    summary = pd.DataFrame(
        [
            {
                "Wellbore": "15/9-F-14",
                "Model": "Exponential",
                "Fit Start": FIT_START.date(),
                "Fit End": FIT_END.date(),
                "Observations": len(df),
                "qi Sm3/d": result["qi"],
                "qi Std Error": result["qi_se"],
                "qi 95% CI Low": result[
                    "qi_ci_low"
                ],
                "qi 95% CI High": result[
                    "qi_ci_high"
                ],
                "D 1/month": result["d"],
                "D Std Error": result["d_se"],
                "D 95% CI Low": result[
                    "d_ci_low"
                ],
                "D 95% CI High": result[
                    "d_ci_high"
                ],
                "Effective Monthly Decline": (
                    effective_monthly_decline
                ),
                "Effective Annual Decline": (
                    effective_annual_decline
                ),
                "Half-Life Months": half_life,
                "RMSE Sm3/d": result["rmse"],
                "MAE Sm3/d": result["mae"],
                "MAPE %": result["mape"],
                "R2": result["r2"],
            }
        ]
    )

    numeric = summary.select_dtypes(
        include=[np.number]
    ).columns

    summary[numeric] = (
        summary[numeric]
        .round(5)
    )

    return summary


def build_threshold_table(
    result,
):
    """Calculate model time to specified technical rate thresholds."""

    qi = result["qi"]
    d = result["d"]

    rows = []

    for threshold in RATE_THRESHOLDS:

        if threshold >= qi:
            months = 0.0
        else:
            months = (
                np.log(
                    qi / threshold
                )
                / d
            )

        date = (
            FIT_START
            + pd.DateOffset(
                months=int(
                    np.ceil(months)
                )
            )
        )

        rows.append(
            {
                "Rate Threshold Sm3/d": (
                    threshold
                ),
                "Months from Fit Start": (
                    months
                ),
                "First Full Month Below Threshold": (
                    date.date()
                ),
            }
        )

    threshold_table = pd.DataFrame(
        rows
    )

    threshold_table[
        "Months from Fit Start"
    ] = (
        threshold_table[
            "Months from Fit Start"
        ].round(2)
    )

    return threshold_table


def create_figure(
    df,
    result,
):
    """Create final fit and residual diagnostic figure."""

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    t_history = (
        df["t_months"]
        .to_numpy(dtype=float)
    )

    t_forecast = np.linspace(
        0.0,
        float(
            t_history.max()
            + FORECAST_MONTHS
        ),
        600,
    )

    dates_forecast = (
        FIT_START
        + pd.to_timedelta(
            t_forecast * 30.4375,
            unit="D",
        )
    )

    q_forecast = exponential(
        t_forecast,
        result["qi"],
        result["d"],
    )

    # Parameter-envelope curves.
    q_high = exponential(
        t_forecast,
        result["qi_ci_high"],
        result["d_ci_low"],
    )

    q_low = exponential(
        t_forecast,
        max(
            result["qi_ci_low"],
            0.0,
        ),
        result["d_ci_high"],
    )

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(11.5, 8.5),
        constrained_layout=True,
        gridspec_kw={
            "height_ratios": [
                2.4,
                1.0,
            ]
        },
    )

    # ---------------------------------------------------------
    # A. Final exponential model
    # ---------------------------------------------------------

    ax = axes[0]

    ax.scatter(
        df["Month"],
        df["Oil Rate Sm3/d"],
        color="black",
        s=32,
        label="Observed oil rate",
        zorder=5,
    )

    ax.plot(
        dates_forecast,
        q_forecast,
        color="#0072B2",
        linewidth=2.2,
        label="Exponential model",
    )

    ax.fill_between(
        dates_forecast,
        q_low,
        q_high,
        color="#56B4E9",
        alpha=0.18,
        label="Parameter uncertainty envelope",
    )

    ax.axvline(
        FIT_END,
        color="#666666",
        linestyle="--",
        linewidth=1.2,
    )

    ax.text(
        FIT_END,
        ax.get_ylim()[1] * 0.90,
        "End of fitted history",
        rotation=90,
        va="top",
        ha="right",
        color="#555555",
    )

    ax.set_title(
        "A. Final exponential decline model",
        loc="left",
        fontweight="bold",
    )

    ax.set_ylabel(
        "Oil rate (Sm³/d)"
    )

    ax.set_ylim(
        bottom=0
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
    )

    # ---------------------------------------------------------
    # B. Residuals
    # ---------------------------------------------------------

    ax = axes[1]

    ax.axhline(
        0.0,
        color="#666666",
        linewidth=1.2,
    )

    ax.scatter(
        df["Month"],
        result["residuals"],
        color="#D55E00",
        s=35,
    )

    ax.set_title(
        "B. Historical fit residuals",
        loc="left",
        fontweight="bold",
    )

    ax.set_ylabel(
        "Observed - fitted\n(Sm³/d)"
    )

    ax.set_xlabel(
        "Date"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.suptitle(
        "15/9-F-14 — Final Exponential Decline Model",
        fontsize=15,
        fontweight="bold",
    )

    png_path = (
        FIGURE_DIR
        / "15_9_F_14_final_exponential_model.png"
    )

    pdf_path = (
        FIGURE_DIR
        / "15_9_F_14_final_exponential_model.pdf"
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


def main():
    """Execute final exponential decline analysis."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    result = fit_final_model(
        df
    )

    summary = build_model_summary(
        df,
        result,
    )

    thresholds = build_threshold_table(
        result
    )

    summary_path = (
        REPORT_DIR
        / "f14_final_exponential_model.csv"
    )

    threshold_path = (
        REPORT_DIR
        / "f14_rate_thresholds.csv"
    )

    summary.to_csv(
        summary_path,
        index=False,
    )

    thresholds.to_csv(
        threshold_path,
        index=False,
    )

    create_figure(
        df,
        result,
    )

    print()
    print(
        "15/9-F-14 FINAL EXPONENTIAL MODEL"
    )
    print()

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print(
        "RATE THRESHOLDS"
    )
    print()

    print(
        thresholds.to_string(
            index=False
        )
    )

    print()

    print(
        "Outputs:"
    )
    print(
        "  {}".format(
            summary_path
        )
    )
    print(
        "  {}".format(
            threshold_path
        )
    )


if __name__ == "__main__":
    main()
