# OPM Flow Compatibility Audit

## Purpose

The publicly released Volve model was originally prepared for ECLIPSE. Before running it with OPM Flow, the deck was audited for structural consistency and simulator-compatibility issues.

The objective was to make only the minimum corrections required for execution while preserving the released reservoir description and development schedule as closely as possible.

## ROCK-region consistency

The deck declared 12 relevant PVT/rock regions but contained 13 `ROCK` records. The surplus record was removed so that the ROCK data were consistent with the declared regional structure. The retained 12 records were not modified.

## RSVD / equilibrium-region consistency

The active equilibrium structure used regions 1-12, while the associated RSVD input contained an additional Region 13 table. Region 13 was removed so that the RSVD data were consistent with the active equilibrium-region definition. Regions 1-12 were retained unchanged.

## Schedule syntax correction

Five well-history records in the January 2015 schedule were not correctly enclosed by the expected `WCONHIST` keyword structure. The required keyword wrapper and termination syntax were restored. The numerical well-control values were not changed.

## Parser compatibility

The full model was executed in OPM Flow using the option `--parsing-strictness=low`.

The audit identified ECLIPSE-specific or incompletely supported constructs, including selected `EQLOPTS` behaviour, `ADDZCORN`, `PRIORITY`, and some restart/output-control keywords.

Successful execution therefore does not imply exact semantic equivalence between every ECLIPSE keyword and OPM Flow.

## ADDZCORN limitation

`ADDZCORN` is particularly important because it can affect grid geometry. Differences in simulator support for geometry operations mean that exact internal equivalence cannot be assumed.

For this reason, the project describes the result as a **cross-simulator reproduction**, not an exact simulator replication.

## Verification strategy

Successful completion of the OPM simulation was not treated as sufficient evidence of compatibility. The reproduced model was compared quantitatively with the released ECLIPSE response at 339 aligned report times using field production rates, cumulative production, field pressure, individual-well oil rates, bottom-hole pressure, and water cut.

## Engineering significance

Simulator migration is not simply a file-conversion exercise. Differences in keyword support, grid operations, numerical controls, and well handling can alter predicted reservoir behaviour.

A defensible migration workflow therefore requires both a documented deck audit and quantitative verification of the resulting reservoir response.
