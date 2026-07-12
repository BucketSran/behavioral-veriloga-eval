# Baseband Offset-and-gain Trim Macro

## Task Contract

Implement one Verilog-A DUT artifact for `Baseband Offset-and-gain Trim Macro`.

- Target artifact: `baseband_offset_gain_trim_macro.va`
- Public top module: `baseband_offset_gain_trim_macro`
- Task level: `L1`
- Circuit category: `baseband_signal_conditioning`

## Public Verilog-A Interface

Declare module `baseband_offset_gain_trim_macro` with positional electrical ports `vin, clk, rst, enable, gain_2, gain_1, gain_0, offset_2, offset_1, offset_0, vout, residual_metric, valid`. All ports are electrical.

`gain_2..gain_0` and `offset_2..offset_0` are sampled unsigned trim codes on rising `clk` edges. `gain_0` and `offset_0` are least significant bits.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: output full-scale level
- `vss = 0.0 V`: output low clamp
- `vcm = 0.45 V`: signal common-mode
- `vth = 0.45 V`: logic threshold
- `gain_base = 0.7`: minimum sampled gain
- `gain_step = 0.1`: gain increment per code
- `offset_lsb = 0.025 V`: offset step around the mid-code
- `tr = 150 ps`: output transition smoothing time

## Required Behavior

- Reset or low `enable` drives `vout` to common mode, clears residual metric, and clears `valid`.
- On each enabled rising `clk`, sample gain and offset trim codes.
- Use `gain = gain_base + gain_step * gain_code`.
- Use signed offset `(offset_code - 3) * offset_lsb`.
- Drive `vout` as the clipped gain-and-offset adjusted input around common mode.
- `residual_metric` reports the absolute output distance from common mode and `valid` marks that a trim sample has occurred.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `baseband_offset_gain_trim_macro.va`.
