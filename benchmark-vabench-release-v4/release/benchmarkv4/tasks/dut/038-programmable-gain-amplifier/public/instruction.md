# Programmable Gain Amplifier

## Task Contract

Implement one Verilog-A DUT artifact for a sampled-gain programmable gain amplifier with clipping indication.

- Target artifact: `programmable_gain_amplifier.va`

## Public Verilog-A Interface

Declare module `programmable_gain_amplifier` with positional ports `clk, rst, gain_sel, vin, out, metric`. All ports are electrical.

- `clk`, `rst`, and `gain_sel` are voltage-coded control inputs.
- `vin` is the analog input around the common-mode level.
- `out` is the gain-scaled and bounded output.
- `metric` indicates output clipping.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: logic threshold for `clk`, `rst`, and `gain_sel`.
- `vcm = 0.45 V`: input and output common-mode reference.
- `gain_low = 0.8`: sampled gain when `gain_sel` is low.
- `gain_high = 2.4`: sampled gain when `gain_sel` is high.
- `vmin = 0.0 V`: lower output clamp.
- `vmax = 0.9 V`: upper output clamp.
- `tr = 200 ps`: transition smoothing time for `out` and `metric`.

## Required Behavior

- Initialize the sampled gain to unity.
- On each rising `clk` crossing, sample `gain_sel` unless reset is active.
- While `rst` is above `vth`, use unity gain, drive `out` to `vcm`, and drive `metric` low.
- When not reset, select `gain_high` for high `gain_sel` and `gain_low` for low `gain_sel`.
- Drive `out` as `vcm + gain * (V(vin) - vcm)` after clipping to the `vmin` to `vmax` range.
- Drive `metric` high when the unclamped target would exceed either clamp limit, and low otherwise.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A. Use voltage contributions only; do not use current contributions, transistor-level devices, AC/noise analysis, or topology-level assumptions. Use a sampled gain state and smooth voltage-domain output transitions. Do not add extra ports, files, debug outputs, pass/fail flags, or state observables that are not part of the public interface.

## Output Contract

Return exactly one complete source artifact named `programmable_gain_amplifier.va`.
