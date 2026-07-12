# Non-overlapping Clock Generator

## Task Contract

Implement one Verilog-A DUT artifact for `Non-overlapping Clock Generator`.

- Target artifact: `nonoverlap_clock_generator.va`
- Public top module: `nonoverlap_clock_generator`
- Task level: `L1`
- Circuit category: `clock_timing`

## Public Verilog-A Interface

Declare module `nonoverlap_clock_generator` with positional electrical ports `clk_in, rst, enable, phi1, phi2, deadtime_metric, valid`. All ports are electrical.

`clk_in`, `rst`, and `enable` are voltage-coded controls. `phi1` and `phi2` are generated non-overlapping phase outputs. `deadtime_metric` marks the enforced both-low handoff interval, and `valid` marks that at least one active phase handoff has completed.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: logic-high output level
- `vss = 0.0 V`: logic-low output level
- `vth = 0.45 V`: logic threshold for input controls
- `dead_ticks = 5`: number of internal timer ticks held both-low after a phase request
- `tick = 200 ps`: internal discrete update interval for dead-time scheduling
- `tr = 100 ps`: output transition smoothing time

## Required Behavior

- Reset or a low `enable` clears both phases, `deadtime_metric`, and `valid`.
- A rising `clk_in` request eventually enables `phi1`; a falling `clk_in` request eventually enables `phi2`.
- During each handoff, both `phi1` and `phi2` remain low for the configured dead-time interval.
- `phi1` and `phi2` must never be high at the same time.
- `deadtime_metric` is high only while a pending phase request is in the enforced both-low interval.
- `valid` becomes high after the first enabled handoff completes and remains high until reset or disable.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `nonoverlap_clock_generator.va`.
