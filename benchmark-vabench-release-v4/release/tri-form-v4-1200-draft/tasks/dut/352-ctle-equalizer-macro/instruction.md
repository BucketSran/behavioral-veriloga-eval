# CTLE Equalizer Macro

## Task Contract

Implement one Verilog-A DUT artifact for `CTLE Equalizer Macro`.

- Target artifact: `ctle_equalizer.va`
- Public top module: `ctle_equalizer`
- Task level: `L1`
- Circuit category: `serdes_equalization_systems`

## Public Verilog-A Interface

Declare module `ctle_equalizer` with positional electrical ports `vin, clk, rst, boost_2, boost_1, boost_0, vout, edge_metric, sat_flag`. All ports are electrical.

`boost_2..boost_0` are sampled as an unsigned boost code on `clk` rising edges. `edge_metric` reports recent edge emphasis magnitude and `sat_flag` marks output clamp activity.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: output full-scale level
- `vss = 0.0 V`: output low/reset level
- `vcm = 0.45 V`: common-mode level
- `vth = 0.45 V`: logic threshold
- `base_gain = 1.0`: low-frequency gain
- `boost_step = 0.08`: edge-emphasis gain per boost code
- `tr = 120 ps`: output transition smoothing time

## Required Behavior

- Reset initializes the equalized output to common mode and clears metric outputs.
- On each rising `clk`, sample the boost code and the current input.
- Drive `vout` from the current input plus a boost-code-scaled edge term relative to the previous sampled input.
- Clamp `vout` to the `vss` to `vdd` range.
- `edge_metric` reports the absolute boosted edge contribution after clipping to full scale.
- `sat_flag` is high when the unclamped equalized target would exceed either output rail.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `ctle_equalizer.va`.
