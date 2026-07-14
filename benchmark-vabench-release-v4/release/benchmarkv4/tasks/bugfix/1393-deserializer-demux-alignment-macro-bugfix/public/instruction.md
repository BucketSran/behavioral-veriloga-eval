# Deserializer DEMUX Alignment Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `deserializer_demux_alignment_macro.va`:
  - Module `deserializer_demux_alignment_macro` (entry)
    - position 0: `clk` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `serial_in` (inout, electrical)
    - position 4: `align_pulse` (inout, electrical)
    - position 5: `out0` (inout, electrical)
    - position 6: `out1` (inout, electrical)
    - position 7: `out2` (inout, electrical)
    - position 8: `out3` (inout, electrical)
    - position 9: `phase_metric` (inout, electrical)
    - position 10: `word_valid` (inout, electrical)

## Public Parameter Contract

- `deserializer_demux_alignment_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `deserializer_demux_alignment_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `deserializer_demux_alignment_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `deserializer_demux_alignment_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `deserializer_demux_alignment_macro.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear all parallel outputs, `phase_metric`, and `word_valid`. Required traces: `time`, `clk`, `rst`, `enable`, `serial_in`, `align_pulse`, `out0`, `out1`, `out2`, `out3`, `phase_metric`, `word_valid`.
- `P_A_RISING_ALIGN_PULSE_RESETS_THE`: restore: A rising `align_pulse` resets the slot pointer so the next sampled serial bit is written to `out0`. Required traces: `time`, `clk`, `rst`, `enable`, `serial_in`, `align_pulse`, `out0`, `out1`, `out2`, `out3`, `phase_metric`, `word_valid`.
- `P_ON_EACH_RISING_CLK_EDGE_WHILE`: restore: On each rising `clk` edge while enabled, sample `serial_in` into the active output slot and advance the slot pointer. Required traces: `time`, `clk`, `rst`, `enable`, `serial_in`, `align_pulse`, `out0`, `out1`, `out2`, `out3`, `phase_metric`, `word_valid`.
- `P_ASSERT_WORD_VALID_AFTER_ALL_FOUR`: restore: Assert `word_valid` after all four output slots have been updated since the most recent alignment event. Required traces: `time`, `clk`, `rst`, `enable`, `serial_in`, `align_pulse`, `out0`, `out1`, `out2`, `out3`, `phase_metric`, `word_valid`.
- `P_PHASE_METRIC_MUST_EXPOSE_THE_ACTIVE`: restore: `phase_metric` must expose the active slot pointer. Required traces: `time`, `clk`, `rst`, `enable`, `serial_in`, `align_pulse`, `out0`, `out1`, `out2`, `out3`, `phase_metric`, `word_valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `deserializer_demux_alignment_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
