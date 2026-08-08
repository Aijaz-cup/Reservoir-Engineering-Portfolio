# Project 01 - Decline Curve Analysis and Production Forecasting

## Objective

Evaluate historical well production performance and develop a technically defensible production forecast using decline curve analysis.

## Engineering Questions

- How has the well's oil, gas, and water production changed with time?
- Which changes represent reservoir decline and which may result from operating conditions?
- What historical period is appropriate for decline curve fitting?
- Which Arps decline model best represents the observed production behavior?
- What production forecast does the selected model predict?
- What are the major uncertainties and limitations of the forecast?

## Methods

The project will evaluate:

- Production data quality
- Oil, gas, and water rate behavior
- Water cut
- Gas-oil ratio
- Cumulative production
- Exponential decline
- Hyperbolic decline
- Harmonic decline
- Production forecasting
- Estimated ultimate recovery
- Forecast uncertainty

## Dataset

The final analysis will use publicly available production data from the Volve field on the Norwegian Continental Shelf.

## Tools

Python | pandas | NumPy | SciPy | Matplotlib | Git

## Production Surveillance

Production histories were evaluated using producing-day oil and water rates, water cut, gas-oil ratio, and monthly uptime.

### Candidate Producer Comparison

![Volve DCA candidate oil-rate comparison](figures/dca_candidate_oil_rate_comparison.png)

Among the evaluated producers, `15/9-F-14` provides the longest sustained post-peak decline behavior with relatively consistent production trends.

### 15/9-F-14 Production Surveillance

![15/9-F-14 production surveillance](figures/15_9_F_14_well_surveillance.png)

The `15/9-F-14` history shows a progressive decline in oil rate accompanied by increasing water cut. Operational uptime variations are considered when selecting the decline-curve fitting interval.

Additional surveillance results for `15/9-F-12` and `15/9-F-11` are available in the `figures` directory.

## Decline Curve Analysis — 15/9-F-14

Detailed production surveillance identified `15/9-F-14` as the primary decline-analysis well.

The selected decline interval extends from **May 2013 through March 2016** and contains 35 monthly observations.

![F-14 decline-regime screening](figures/15_9_F_14_decline_regime_screening.png)

### Model Selection

Exponential, harmonic, and hyperbolic Arps models were evaluated using chronological calibration and validation.

The hyperbolic solution converged to approximately \(b=0\), while the harmonic model showed substantially poorer validation performance. The exponential model was retained.

\[
q_o(t)=908.07\,e^{-0.05610t}
\]

with \(t\) in months from May 2013.

Key model statistics:

- \(D = 0.05610\) month⁻¹
- Effective annual decline = 48.99%
- \(R^2 = 0.9893\)
- RMSE = 23.49 Sm³/d
- MAPE = 4.76%

![F-14 Arps model comparison](figures/15_9_F_14_arps_model_comparison.png)

### Uptime Sensitivity

Excluding months with uptime below 90% changes the fitted decline constant by only 0.61%.

![F-14 uptime sensitivity](figures/15_9_F_14_uptime_sensitivity.png)

### Production Forecast

Historical cumulative oil through March 2016 is approximately **3.9315 million Sm³**.

Terminal-rate sensitivity was evaluated for 100, 75, 50, and 25 Sm³/d. These rates are technical forecast assumptions rather than economic limits.

![F-14 production forecast](figures/15_9_F_14_terminal_rate_forecast.png)

Detailed results are provided in [`report/DCA_RESULTS.md`](report/DCA_RESULTS.md).
