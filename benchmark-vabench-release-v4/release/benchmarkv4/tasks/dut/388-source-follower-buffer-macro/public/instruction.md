# Source-follower Buffer Macro

## Task Contract

Implement one Verilog-A DUT artifact for `Source-follower Buffer Macro`.

- Target artifact: `source_follower_buffer_macro.va`
- Public top module: `source_follower_buffer_macro`
- Task level: `L1`
- Circuit category: `analog_primitive`

## Public Verilog-A Interface

Declare module `source_follower_buffer_macro` with positional electrical ports `vin, vbias, enable, rst, vout, headroom_metric, valid`. All ports are electrical.

`vin` is the signal input and `vbias` is the available source-follower bias/headroom rail. `enable` and `rst` are voltage-coded controls.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: nominal high level for flags
- `vss = 0.0 V`: low/reset clamp
- `vth = 0.45 V`: logic threshold
- `vgs_drop = 0.12 V`: source-follower offset from input to output
- `min_headroom = 0.10 V`: minimum bias headroom above output
- `tr = 150 ps`: output transition smoothing time

## Required Behavior

- Reset or low `enable` drives the output and metrics low.
- When enabled, the output follows `vin - vgs_drop`.
- Clamp the output between `vss` and `vbias - min_headroom`.
- `headroom_metric` reports the remaining `vbias - vout` margin clipped to the nominal flag range.
- `valid` is high only when enabled, not reset, and the bias rail can support at least the minimum headroom.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `source_follower_buffer_macro.va`.
