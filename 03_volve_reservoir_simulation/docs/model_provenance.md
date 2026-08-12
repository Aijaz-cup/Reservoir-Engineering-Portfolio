# Model Provenance

## Source model

This project uses the publicly released Volve reservoir simulation model as the reference reservoir model.

The original model was prepared for ECLIPSE and already contains the geological model, petrophysical properties, PVT description, relative-permeability functions, well definitions, development schedule, and the calibration/history-matching work associated with the released model.

The purpose of this project was **not to perform a new history match**.

Instead, the work focused on:

1. auditing the released simulation deck;
2. adapting the model sufficiently for execution in OPM Flow;
3. reproducing the released ECLIPSE response;
4. quantifying cross-simulator differences at field and well scales; and
5. extending the reproduced model through controlled reservoir-sensitivity studies.

## Reference and reproduced simulations

Two simulator responses are compared:

- **Released ECLIPSE reference**
- **OPM Flow reproduction**

The comparison was performed at 339 common report times spanning simulation day 11 to day 3197.

Because the same reporting times were used, calculated differences are direct like-for-like comparisons rather than interpolated comparisons between different dates.

## Unit system

The released reservoir deck specifies the `METRIC` unit system.

Accordingly, the public figures use metric reservoir-engineering units, including:

- liquid rates: Sm³/d
- cumulative liquid production: Sm³
- gas rates: Sm³/d
- cumulative gas production: Sm³
- pressure: bar
- water cut: dimensionless fraction

## Scope of interpretation

Agreement between OPM Flow and the released ECLIPSE model is interpreted as **cross-simulator reproducibility of the released model response**.

It should not be interpreted as an independent validation of the geological model or as evidence that either simulator represents the physical reservoir exactly.
