"""Uptime sensitivity analysis for the selected F-14 exponential decline model."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


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

UPTIME_THRESHOLD = 0.90


def exponential(t, qi, di):
    """Exponential decline model."""

    return qi * np.exp(-di * t)


def load_data():
    """Load the selected decline interval."""

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

    df["t_months"] = np.arange(
        len(df),
        dtype=float,
    )

    return df


def fit_exponential(df):
    """Fit the exponential model to supplied observations."""

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

    di_guess = max(
        -float(slope),
        1.0e-5,
    )

    parameters, covariance = curve_fit(
        exponential,
        t,
        q,
        p0=[
            float(q[0]),
            di_guess,
        ],
        bounds=(
            [0.0, 0.0],
            [np.inf, 5.0],
        ),
        maxfev=50000,
    )

    prediction = exponential(
        t,
        *parameters
    )

    residual = q - prediction

    rmse = float(
        np.sqrt(
            np.mean(
                residual ** 2
            )
        )
    )

    mae = float(
        np.mean(
            np.abs(residual)
        )
    )

    mape = float(
        np.mean(
            np.abs(
                residual / q
            )
        )
        * 100.0
    )

    ss_res = float(
        np.sum(
            residual ** 2
        )
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
        1.0 - ss_res / ss_tot
    )

    standard_errors = np.sqrt(
        np.diag(covariance)
    )

    return {
        "qi": float(parameters[0]),
        "Di": float(parameters[1]),
        "qi_se": float(standard_errors[0]),
        "Di_se": float(standard_errors[1]),
        "RMSE": rmse,
        "MAE": mae,
        "MAPE": mape,
        "R2": r2,
    }


def build_summary(
    all_data,
    high_uptime,
):
    """Build model-parameter sensitivity table."""

    baseline = fit_exponential(
        all_data
    )

    filtered = fit_exponential(
        high_uptime
    )

    rows = []

    for name, frame, result in [
        (
            "All selected months",
            all_data,
            baseline,
        ),
        (
            "Uptime >= 0.90",
            high_uptime,
            filtered,
        ),
    ]:

        effective_monthly_decline = (
            1.0
            - np.exp(
                -result["Di"]
            )
        )

        effective_annual_decline = (
            1.0
            - np.exp(
                -12.0
                * result["Di"]
            )
        )

        half_life_months = (
            np.log(2.0)
            / result["Di"]
        )

        rows.append(
            {
                "Case": name,
                "Observations": len(frame),
                "qi Sm3/d": result["qi"],
                "qi Std Error": result["qi_se"],
                "Di 1/month": result["Di"],
                "Di Std Error": result["Di_se"],
                "Effective Monthly Decline": (
                    effective_monthly_decline
                ),
                "Effective Annual Decline": (
                    effective_annual_decline
                ),
                "Half-Life Months": (
                    half_life_months
                ),
                "RMSE Sm3/d": result["RMSE"],
                "MAE Sm3/d": result["MAE"],
                "MAPE %": result["MAPE"],
                "R2": result["R2"],
            }
        )

    summary = pd.DataFrame(
        rows
    )

    baseline_di = float(
        summary.loc[
            summary["Case"]
            == "All selected months",
            "Di 1/month",
        ].iloc[0]
    )

    filtered_di = float(
        summary.loc[
            summary["Case"]
            == "Uptime >= 0.90",
            "Di 1/month",
        ].iloc[0]
    )

    baseline_qi = float(
        summary.loc[
            summary["Case"]
            == "All selected months",
            "qi Sm3/d",
        ].iloc[0]
    )

    filtered_qi = float(
        summary.loc[
            summary["Case"]
            == "Uptime >= 0.90",
            "qi Sm3/d",
        ].iloc[0]
    )

    summary["Di Change vs Baseline %"] = [
        0.0,
        (
            filtered_di
            - baseline_di
        )
        / baseline_di
        * 100.0,
    ]

    summary["qi Change vs Baseline %"] = [
        0.0,
        (
            filtered_qi
            - baseline_qi
        )
        / baseline_qi
        * 100.0,
    ]

    numeric = summary.select_dtypes(
        include=[np.number]
    ).columns

    summary[numeric] = (
        summary[numeric]
        .round(5)
    )

    return summary


def create_figure(
    data,
    high_uptime,
):
    """Plot full-history and high-uptime exponential fits."""

    full_fit = fit_exponential(
        data
    )

    high_fit = fit_exponential(
        high_uptime
    )

    t_dense = np.linspace(
        float(data["t_months"].min()),
        float(data["t_months"].max()),
        400,
    )

    dates_dense = (
        FIT_START
        + pd.to_timedelta(
            t_dense * 30.4375,
            unit="D",
        )
    )

    q_full = exponential(
        t_dense,
        full_fit["qi"],
        full_fit["Di"],
    )

    q_high = exponential(
        t_dense,
        high_fit["qi"],
        high_fit["Di"],
    )

    low_uptime = data.loc[
        data["Uptime Fraction"]
        < UPTIME_THRESHOLD
    ]

    fig, ax = plt.subplots(
        figsize=(11, 6.5),
        constrained_layout=True,
    )

    ax.scatter(
        high_uptime["Month"],
        high_uptime["Oil Rate Sm3/d"],
        color="black",
        s=35,
        label="Uptime >= 90%",
        zorder=5,
    )

    ax.scatter(
        low_uptime["Month"],
        low_uptime["Oil Rate Sm3/d"],
        color="#D55E00",
        marker="x",
        s=55,
        linewidth=1.8,
        label="Uptime < 90%",
        zorder=6,
    )

    ax.plot(
        dates_dense,
        q_full,
        color="#0072B2",
        linewidth=2.2,
        label="Fit: all selected months",
    )

    ax.plot(
        dates_dense,
        q_high,
        color="#009E73",
        linestyle="--",
        linewidth=2.2,
        label="Fit: uptime >= 90%",
    )

    ax.set_title(
        "15/9-F-14 — Exponential Decline Uptime Sensitivity",
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

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
    )

    png_path = (
        FIGURE_DIR
        / "15_9_F_14_uptime_sensitivity.png"
    )

    pdf_path = (
        FIGURE_DIR
        / "15_9_F_14_uptime_sensitivity.pdf"
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
    """Execute the uptime sensitivity analysis."""

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = load_data()

    high_uptime = data.loc[
        data["Uptime Fraction"]
        >= UPTIME_THRESHOLD
    ].copy()

    summary = build_summary(
        data,
        high_uptime,
    )

    output_path = (
        REPORT_DIR
        / "f14_uptime_sensitivity.csv"
    )

    summary.to_csv(
        output_path,
        index=False,
    )

    create_figure(
        data,
        high_uptime,
    )

    print()
    print(
        "15/9-F-14 UPTIME SENSITIVITY"
    )
    print()

    print(
        summary.to_string(
            index=False
        )
    )

    print()

    print(
        "Excluded months:"
    )

    print(
        data.loc[
            data["Uptime Fraction"]
            < UPTIME_THRESHOLD,
            [
                "Month",
                "Uptime Fraction",
                "Oil Rate Sm3/d",
            ],
        ].to_string(
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
