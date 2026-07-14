# Track/Hold with Droop and Aperture Metric

## Task Contract

Implement one Verilog-A DUT artifact for `Track/Hold with Droop and Aperture Metric`.

- Target artifact(s):
- `track_hold_aperture.va`
- Public top module: `track_hold_aperture`
- Task level: `L1`
- Circuit category: `sampling_memory`

## Public Verilog-A Interface

Declare top module `track_hold_aperture` with positional electrical ports `vin, track, rst, enable, vhold, aperture_metric, droop_metric, valid`. All public ports are electrical.

`track`, `rst`, and `enable` are voltage-coded controls. Falling `track` edges enter hold mode and expose the sampled value, aperture metric, and droop metric.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and any relevant child modules:

- `vdd = 0.9 V`: logic-high and metric full-scale level
- `vss = 0.0 V`: logic-low and minimum held output level
- `vth = 0.45 V`: logic threshold
- `tick = 1 ns`: internal update period
- `droop_per_tick = 15 mV`: hold-mode droop per update tick
- `aperture_gain = 0.6`: gain from sample step magnitude to aperture metric
- `tr = 100 ps`: output transition smoothing time

## Required Behavior

- Reset or a low `enable` clears the held output, aperture metric, droop metric, and valid flag.
- While `track` is high, the held state tracks the input at the internal update cadence and `valid` remains low.
- On a falling `track` edge, sample `vin`, assert `valid`, and report an aperture metric proportional to the step from the previous tracked value.
- During hold mode, the held output droops downward by `droop_per_tick` on each update tick without going below `vss`.
- `droop_metric` accumulates the total hold-mode droop and clears on a new sample, reset, or disable.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra public ports, debug-only files, simulation decks, generated result files, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `track_hold_aperture.va`.
