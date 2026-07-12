# Programmable Clock Skew Aligner Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `programmable_clock_skew_aligner.va`:
  - Module `programmable_clock_skew_aligner` (entry)
    - position 0: `clk_in` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `skew_2` (inout, electrical)
    - position 4: `skew_1` (inout, electrical)
    - position 5: `skew_0` (inout, electrical)
    - position 6: `clk_out` (inout, electrical)
    - position 7: `delay_metric` (inout, electrical)
    - position 8: `valid` (inout, electrical)

## Public Parameter Contract

- `programmable_clock_skew_aligner.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `programmable_clock_skew_aligner.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `programmable_clock_skew_aligner.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `programmable_clock_skew_aligner.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `programmable_clock_skew_aligner.unit_delay_metric` defaults to `0.1`; valid range: finite; overrides unit_delay_metric.
- `programmable_clock_skew_aligner.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive output and metrics low. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.
- `P_DECODE_SKEW_2_SKEW_0_AS`: restore: Decode `skew_2..skew_0` as a programmable output-edge delay code. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.
- `P_FOR_EACH_ACCEPTED_INPUT_CLOCK_EDGE`: restore: For each accepted input clock edge, schedule one output edge after the code-dependent delay. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.
- `P_EXPOSE_THE_ACTIVE_DELAY_CODE_AS`: restore: Expose the active delay code as `delay_metric`. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.
- `P_ASSERT_VALID_AFTER_THE_FIRST_DELAYED`: restore: Assert `valid` after the first delayed output edge has been generated. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `programmable_clock_skew_aligner.va`.
Every supplied `.va` file is editable; do not add or omit files.
