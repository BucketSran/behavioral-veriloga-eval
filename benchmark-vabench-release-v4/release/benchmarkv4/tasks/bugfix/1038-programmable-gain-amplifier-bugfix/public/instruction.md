# Programmable Gain Amplifier Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `programmable_gain_amplifier.va`:
  - Module `programmable_gain_amplifier` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `gain_sel` (input, electrical)
    - position 3: `vin` (input, electrical)
    - position 4: `out` (output, electrical)
    - position 5: `metric` (output, electrical)

## Public Parameter Contract

- `programmable_gain_amplifier.vth` defaults to `0.45` V; valid range: vmin < vth < vmax; sets clk, rst, and gain_sel logic threshold.
- `programmable_gain_amplifier.vcm` defaults to `0.45` V; valid range: vmin <= vcm <= vmax; sets the input and output common-mode reference.
- `programmable_gain_amplifier.gain_low` defaults to `0.8`; valid range: gain_low > 0; sets the sampled low-gain transfer slope.
- `programmable_gain_amplifier.gain_high` defaults to `2.4`; valid range: gain_high > 0; sets the sampled high-gain transfer slope.
- `programmable_gain_amplifier.vmin` defaults to `0.0` V; valid range: vmin < vmax; sets the lower output clamp.
- `programmable_gain_amplifier.vmax` defaults to `0.9` V; valid range: vmax > vmin; sets the upper output clamp.
- `programmable_gain_amplifier.tr` defaults to `2e-10` s; valid range: tr > 0; sets out and metric transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_UNITY`: restore: While rst is active, the sampled gain is unity, out is vcm, and metric is low. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_SAMPLED_GAIN_SELECT`: restore: Each rising clk crossing with reset inactive samples gain_sel, selecting gain_high above vth and gain_low below vth; the selection holds between crossings. Required traces: `time`, `clk`, `rst`, `gain_sel`, `vin`, `out`.
- `P_COMMON_MODE_GAIN`: restore: The unclamped output target is vcm plus the sampled gain times vin minus vcm. Required traces: `time`, `vin`, `out`.
- `P_OUTPUT_CLAMP`: restore: Out is limited to the inclusive vmin through vmax range with finite smoothing. Required traces: `time`, `out`.
- `P_CLIP_METRIC`: restore: Metric is high exactly when the unclamped target lies outside vmin through vmax, and low otherwise; reset forces it low. Required traces: `time`, `rst`, `vin`, `out`, `metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavior with sampled gain state.
- Use voltage contributions only and finite smoothing for driven outputs.
- Do not add undeclared ports, files, debug outputs, pass/fail flags, or validation state.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `programmable_gain_amplifier.va`.
Every supplied `.va` file is editable; do not add or omit files.
