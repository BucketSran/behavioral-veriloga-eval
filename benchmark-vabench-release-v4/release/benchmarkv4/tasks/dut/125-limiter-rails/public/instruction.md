# Limiter Rails

## Task Contract

Implement the requested Verilog-A artifact for `Limiter Rails`.
- Form: `dut`
- Level: `L1`
- Category: `mixed_signal`
- Target artifact(s): `limiter_rails.va`

- Base function: Supply-referenced voltage limiter
- Domain: `voltage`
- Output boundary: validation logic is external; do not generate validation harness or testbench, or measurement helper artifacts.

## Public Verilog-A Interface

`limiter_rails.va` must declare:

```verilog
module limiter_rails(vdd, vss, vin, vmax, vmin, vout);
input vdd, vss, vin, vmax, vmin;
output vout;
electrical vdd, vss, vin, vmax, vmin, vout;
```

## Public Parameter Contract

This task has no public parameters.

## Required Behavior

- `P_RAIL_DERIVED_LIMITS`: Derive the upper limit as `V(vdd) - V(vmax)` and the lower limit as `V(vss) + V(vmin)`.

- `P_PASS_WITHIN_LIMITS`: When `V(vin)` lies between the derived limits, drive `vout` to `V(vin)`.

- `P_LIMIT_ABOVE_UPPER`: When `V(vin)` exceeds the upper limit, drive `vout` to the upper limit.

- `P_LIMIT_BELOW_LOWER`: When `V(vin)` is below the lower limit, drive `vout` to the lower limit.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `limiter_rails.va`.
Do not include explanatory prose outside the source artifact contents.
