# Reservoir Sensitivity Design

## Objective

After reproducing the released ECLIPSE model response with OPM Flow, three controlled reservoir sensitivities were evaluated:

1. fault connectivity;
2. local permeability around producer P-F-12;
3. north-side pore volume.

The purpose was to examine how selected geological and flow-property assumptions influence reservoir performance.

The Low/Base/High cases are deterministic engineering screening scenarios. They are not probabilistic P10/P50/P90 realizations.

## Sensitivity matrix

| Sensitivity | Low | Base | High |
|---|---:|---:|---:|
| Fault connectivity multiplier | 0.02 | 0.06 | 0.18 |
| P-F-12 local permeability multiplier | 0.15 | 0.30 | 0.60 |
| North-side pore-volume multiplier | 1.00 | 1.30 | 1.60 |

## Fault connectivity

The selected fault-transmissibility parameter was modified to test the influence of inter-compartment communication.

Engineering question:

**How strongly does the selected fault connection influence pressure communication and field production?**

The Low and High cases changed only the targeted fault-connectivity definition relative to the Base case.

## P-F-12 local permeability

The local permeability sensitivity modified the targeted `PERMX`, `PERMY`, and `PERMZ` definitions around producer P-F-12.

Engineering question:

**How does local reservoir conductivity influence well performance, pressure drawdown and field production?**

This sensitivity is particularly useful for examining the interaction between reservoir properties and well-control constraints.

## North-side pore volume

The pore-volume sensitivity modified selected pore-volume definitions in the northern part of the model.

Engineering question:

**How does changing connected reservoir storage influence displacement behaviour and cumulative recovery?**

## Response quantities

Field-scale responses included:

- FOPR — field oil production rate
- FWPR — field water production rate
- FOPT — field cumulative oil production
- FWPT — field cumulative water production
- FGPT — field cumulative gas production
- FPR — field pressure

Additional P-F-12 diagnostics included:

- WOPR — well oil production rate
- WOPT — well cumulative oil production
- WWCT — water cut
- WWPT — well cumulative water production
- WBHP — bottom-hole pressure

## Relative-response metric

For any response quantity X, the change relative to Base is

Delta X (%) = 100 x (X_case - X_base) / X_base

Positive values indicate an increase relative to the Base case; negative values indicate a decrease.

## Final cumulative-oil response

| Sensitivity | Low vs Base | High vs Base |
|---|---:|---:|
| North-side pore volume | -0.681% | +0.615% |
| P-F-12 local permeability | -0.394% | +0.314% |
| Fault connectivity | -0.081% | +0.006% |

Within the tested parameter ranges, north-side pore volume produced the largest final FOPT response, followed by P-F-12 local permeability.

The selected fault-connectivity perturbation produced comparatively little change in final cumulative oil.

## Time-dependent response

Final cumulative production alone does not reveal when a sensitivity begins to influence reservoir behaviour.

For this reason, the north-side pore-volume cases were also compared through time using the percentage deviation in FOPT relative to the Base case.

The Low and High pore-volume cases remain close to Base during the early production period and progressively diverge later in the development history.

## Interpretation caution

The sensitivity ranking is range-dependent.

The results do not establish that pore volume is universally more important than permeability or fault connectivity.

They show only that, for the specific perturbations investigated in this study, the north-side pore-volume cases generated the largest final cumulative-oil response.
