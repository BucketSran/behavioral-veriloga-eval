# CTLE Equalizer Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ctle_equalizer.va`:
  - Module `ctle_equalizer` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `boost_2` (input, electrical)
    - position 4: `boost_1` (input, electrical)
    - position 5: `boost_0` (input, electrical)
    - position 6: `vout` (output, electrical)
    - position 7: `edge_metric` (output, electrical)
    - position 8: `sat_flag` (output, electrical)

## Public Parameter Contract

- `ctle_equalizer.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `ctle_equalizer.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `ctle_equalizer.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `ctle_equalizer.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `ctle_equalizer.base_gain` defaults to `1.0`; valid range: finite; overrides base_gain.
- `ctle_equalizer.boost_step` defaults to `0.08`; valid range: finite; overrides boost_step.
- `ctle_equalizer.tr` defaults to `120p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_INITIALIZES_THE_EQUALIZED_OUTPUT_TO`: restore: Reset initializes the equalized output to common mode and clears metric outputs. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_ON_EACH_RISING_CLK_SAMPLE_THE`: restore: On each rising `clk`, sample the boost code and the current input. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_DRIVE_VOUT_FROM_THE_CURRENT_INPUT`: restore: Drive `vout` from the current input plus a boost-code-scaled edge term relative to the previous sampled input. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_CLAMP_VOUT_TO_THE_VSS_TO`: restore: Clamp `vout` to the `vss` to `vdd` range. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_EDGE_METRIC_REPORTS_THE_ABSOLUTE_BOOSTED`: restore: `edge_metric` reports the absolute boosted edge contribution after clipping to full scale. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_SAT_FLAG_IS_HIGH_WHEN_THE`: restore: `sat_flag` is high when the unclamped equalized target would exceed either output rail. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ctle_equalizer.va`.
Every supplied `.va` file is editable; do not add or omit files.
