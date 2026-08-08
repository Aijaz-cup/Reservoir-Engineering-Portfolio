# Decline Curve Analysis — Volve 15/9-F-14

## Production History Screening

Production histories for 15/9-F-12, 15/9-F-14, and 15/9-F-11 were evaluated using producing-day oil and water rates, water cut, gas-oil ratio, monthly uptime, choke position, and pressure measurements.

15/9-F-14 was selected for detailed decline analysis because it provides a long post-peak production history with a sustained oil-rate decline and comparatively stable late-life operating conditions.

## Decline-Regime Selection

The selected decline interval is:

**May 2013 through March 2016**

The interval contains 35 monthly observations.

Key characteristics are:

| Parameter | Value |
|---|---:|
| Initial oil rate | 905.08 Sm³/d |
| Final oil rate | 122.13 Sm³/d |
| Oil-rate reduction | 86.51% |
| Initial water cut | 79.84% |
| Final water cut | 96.32% |
| Median uptime | 98.40% |
| Minimum uptime | 80.62% |
| Median choke position | 96.98% |
| Choke range | 90.18–99.93% |
| Declining month-to-month transitions | 82.35% |
| Linear ln(q) versus time R² | 0.9897 |

The selected period is characterized by sustained oil-rate decline while the choke remains predominantly open. Water cut increases progressively through the interval.

Operational conditions change after March 2016, including substantial choke reduction and lower uptime. Those observations are excluded from the fitted decline regime.

## Arps Model Comparison

Exponential, harmonic, and hyperbolic Arps models were compared using a chronological calibration-validation procedure.

Calibration period:

**May 2013 through September 2015**

Validation period:

**October 2015 through March 2016**

| Model | Calibration R² | Calibration AICc | Validation RMSE (Sm³/d) | Validation MAPE |
|---|---:|---:|---:|---:|
| Exponential | 0.9859 | 192.35 | 8.52 | 4.86% |
| Hyperbolic | 0.9859 | 194.85 | 8.52 | 4.85% |
| Harmonic | 0.9464 | 231.06 | 76.71 | 50.64% |

The hyperbolic fit converges to approximately \(b=0\), reducing to exponential behavior. The additional hyperbolic parameter therefore provides no material improvement.

The exponential model is retained.

## Final Exponential Model

The final model fitted to all 35 selected observations is:

\[
q_o(t)=908.07\,e^{-0.05610t}
\]

where:

- \(q_o\) is producing-day oil rate in Sm³/d;
- \(t\) is time in months from May 2013;
- \(q_i=908.07\) Sm³/d;
- \(D=0.05610\) month⁻¹.

Model statistics:

| Parameter | Value |
|---|---:|
| \(q_i\) | 908.07 Sm³/d |
| \(q_i\) 95% CI | 884.61–931.53 Sm³/d |
| \(D\) | 0.05610 month⁻¹ |
| \(D\) 95% CI | 0.05368–0.05852 month⁻¹ |
| Effective monthly decline | 5.46% |
| Effective annual decline | 48.99% |
| Rate half-life | 12.36 months |
| RMSE | 23.49 Sm³/d |
| MAE | 17.08 Sm³/d |
| MAPE | 4.76% |
| \(R^2\) | 0.9893 |

## Uptime Sensitivity

The exponential model was refitted after excluding months with uptime below 90%.

| Case | Observations | \(q_i\) (Sm³/d) | \(D\) (month⁻¹) | MAPE | \(R^2\) |
|---|---:|---:|---:|---:|---:|
| All selected months | 35 | 908.07 | 0.05610 | 4.76% | 0.9893 |
| Uptime ≥ 90% | 27 | 922.42 | 0.05644 | 4.49% | 0.9899 |

Excluding lower-uptime months changes \(D\) by only 0.61% and \(q_i\) by 1.58%. The estimated decline rate is therefore not materially sensitive to these months.

## Terminal-Rate Sensitivity

Historical cumulative oil production through March 2016 is:

\[
N_{p,\mathrm{hist}}=3.9315\ \mathrm{million\ Sm^3}
\]

or approximately:

\[
24.73\ \mathrm{MMstb}
\]

The exponential model predicts an April 2016 oil rate of approximately 127.46 Sm³/d.

| Terminal rate | Incremental forecast oil | Projected cumulative oil |
|---:|---:|---:|
| 100 Sm³/d | 14,900 Sm³ | 3.9464 million Sm³ |
| 75 Sm³/d | 28,464 Sm³ | 3.9600 million Sm³ |
| 50 Sm³/d | 42,028 Sm³ | 3.9735 million Sm³ |
| 25 Sm³/d | 55,592 Sm³ | 3.9871 million Sm³ |

Extending the terminal rate from 100 Sm³/d to 25 Sm³/d adds approximately 40,692 Sm³ of forecast oil.

The terminal-rate cases are technical forecast sensitivities and are not economic limits.

## Technical Interpretation

The selected F-14 decline interval exhibits a sustained oil-rate decline under predominantly high choke opening and high monthly uptime. The decline occurs simultaneously with increasing water cut, indicating mature waterflood production behavior.

The exponential model provides the most parsimonious representation of the selected decline regime. Chronological validation supports the fitted trend, and the estimated decline parameter remains stable when lower-uptime months are excluded.

The terminal-rate sensitivity shows that only a relatively small volume of oil remains under continued exponential decline because most cumulative production occurred before the forecast start date.

## Limitations

Decline curve analysis is an empirical production-forecasting method and does not explicitly represent reservoir pressure, saturation distribution, relative permeability, well intervention, or facility constraints.

The reported downhole-pressure measurements are flowing well measurements and are not interpreted as average reservoir pressure.

Forecasts after March 2016 represent continuation of the selected decline regime. Subsequent observed operating-condition changes are not represented by the extrapolated decline model.

A terminal production rate should not be interpreted as an economic limit without explicit economic assumptions.
