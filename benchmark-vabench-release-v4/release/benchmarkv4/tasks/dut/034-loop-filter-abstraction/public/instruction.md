# Sampled Loop-Filter Abstraction

## Task Contract

Implement the requested Verilog-A artifact for `Loop Filter Abstraction`.
- Form: `dut`
- Level: `L1`
- Category: `pll_clock_timing`
- Target artifact(s): `loop_filter_abstraction.va`

Implement `loop_filter_abstraction.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module loop_filter_abstraction(
    input  electrical clk,
    input  electrical rst,
    input  electrical vin,
    output electrical out,
    output electrical metric
);
```

## Public Parameter Contract

Provide these overrideable public parameters:

| Parameter | Default | Unit / Range | Contract |
| --- | ---: | --- | --- |
| `tr` | `100 ps` | time, `(0:inf)` | Rise/fall smoothing for `out` and `metric`. |
| `deadband` | `0.05` | V, `[0:inf)` | Input-error magnitude below which loop updates hold state. |

## Required Behavior

The module is a sampled/event-driven PLL loop-filter abstraction that approximates proportional and integral loop-control trends without modeling a transistor-level or KCL/KVL RC network.

- Treat `clk` and `rst` as voltage-coded logic with a 0.45 V threshold.
- Interpret `vin` as a signed loop-error stimulus around 0.45 V.
- Initialize and reset the proportional state to `0.45 V`, the proportional step to `0.20 V`, the integral residual to `0`, the accepted-update count to `0`, and `metric` to `0 V`.
- On each rising `clk` crossing, compute `err = V(vin) - 0.45`.
- When reset is low and `abs(err) > deadband`, accept an update: increase the proportional state by the current step for positive `err`, decrease it by the current step for negative `err`, then accumulate `integral += 0.04 * err`.
- After each accepted update, halve the step and increment the accepted-update count.
- Clamp the proportional state to `[0.05 V, 0.85 V]`.
- Drive `out` from the proportional state plus the accumulated integral residual.
- Drive `metric` to `0.9 V` once the accepted-update count reaches `4`, otherwise keep it at `0 V`. Reset clears the count and metric.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, `ddt()`,
`idt()`, transistor-level devices, AC/noise analysis, validation logic, validation-only
test hooks, or simulator-specific side channels. Use `transition(...)` for the
driven output voltages.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `loop_filter_abstraction.va`.
