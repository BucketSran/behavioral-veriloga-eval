# 3-tap FFE Transmitter

## Task Contract

Implement one Verilog-A DUT artifact for `3-tap FFE Transmitter`.

- Target artifact: `ffe_tx_3tap.va`
- Public top module: `ffe_tx_3tap`
- Task level: `L1`
- Circuit category: `serdes_equalization_systems`

## Public Verilog-A Interface

Declare module `ffe_tx_3tap` with positional electrical ports `data, clk, rst, pre_1, pre_0, post_1, post_0, vout, main_dbg, pre_dbg, post_dbg`. All ports are electrical.

`data` is sampled as a binary NRZ symbol on rising `clk` edges. `pre_1:pre_0` and `post_1:post_0` are unsigned two-bit tap-control codes.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: output full-scale level
- `vss = 0.0 V`: output low level
- `vcm = 0.45 V`: common-mode level
- `vth = 0.45 V`: logic threshold
- `main_amp = 0.18 V`: main cursor amplitude around common mode
- `tap_step = 0.04 V`: tap contribution per code step
- `tr = 120 ps`: output transition smoothing time

## Required Behavior

- Reset clears symbol history and drives all outputs to common mode.
- On each rising `clk`, sample `data` as +1 for high and -1 for low.
- Drive `main_dbg`, `pre_dbg`, and `post_dbg` as voltage-coded per-tap contributions around common mode.
- `vout` is the clipped sum of the current main contribution, previous-symbol pre contribution, and older-symbol post contribution.
- Higher tap-control codes must increase the corresponding contribution magnitude.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `ffe_tx_3tap.va`.
