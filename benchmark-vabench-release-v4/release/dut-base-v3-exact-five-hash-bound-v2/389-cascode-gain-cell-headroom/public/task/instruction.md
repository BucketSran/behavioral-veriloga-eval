# Cascode Gain-cell Headroom Macro

## Task Contract

Implement one Verilog-A DUT artifact for `Cascode Gain-cell Headroom Macro`.

- Target artifact: `cascode_gain_cell_headroom.va`
- Public top module: `cascode_gain_cell_headroom`
- Task level: `L1`
- Circuit category: `analog_primitive`

## Public Verilog-A Interface

Declare module `cascode_gain_cell_headroom` with positional electrical ports `vin, vbias, vdd_sense, enable, rst, vout, gain_metric, headroom_ok`. All ports are electrical.

`vdd_sense` is the available output rail and `vbias` sets the cascode headroom limit. `enable` and `rst` are voltage-coded controls.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vss = 0.0 V`: low clamp
- `vcm = 0.45 V`: input/output common-mode reference
- `vth = 0.45 V`: logic threshold
- `gain = 1.8`: small-signal inverting gain around common mode
- `headroom_drop = 0.16 V`: required output headroom below the lower of `vbias` and `vdd_sense`
- `tr = 150 ps`: output transition smoothing time

## Required Behavior

- Reset or low `enable` drives `vout` to common mode and clears metrics.
- When enabled, compute an inverting gain-cell output around common mode.
- Clamp the output between `vss` and the available headroom limit.
- `gain_metric` reports the absolute output excursion from common mode.
- `headroom_ok` is high only when the available headroom limit remains above common mode.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `cascode_gain_cell_headroom.va`.
