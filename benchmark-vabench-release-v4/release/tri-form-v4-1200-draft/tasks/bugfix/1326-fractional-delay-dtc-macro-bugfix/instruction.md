# Fractional-delay DTC Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `fractional_delay_dtc_macro.va`:
  - Module `fractional_delay_dtc_macro` (entry)
    - position 0: `clk_in` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `frac_3` (inout, electrical)
    - position 4: `frac_2` (inout, electrical)
    - position 5: `frac_1` (inout, electrical)
    - position 6: `frac_0` (inout, electrical)
    - position 7: `clk_out` (inout, electrical)
    - position 8: `phase_metric` (inout, electrical)
    - position 9: `valid` (inout, electrical)

## Public Parameter Contract

- `fractional_delay_dtc_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `fractional_delay_dtc_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `fractional_delay_dtc_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `fractional_delay_dtc_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `fractional_delay_dtc_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `fractional_delay_dtc_macro.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear output, phase metric, and `valid`. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.
- `P_DECODE_FRAC_3_FRAC_0_AS`: restore: Decode `frac_3..frac_0` as a fractional delay setting. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.
- `P_FOR_EACH_INPUT_EDGE_EMIT_ONE`: restore: For each input edge, emit one output edge with a delay proportional to the fractional code. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.
- `P_EXPOSE_THE_FRACTIONAL_DELAY_AS_PHASE`: restore: Expose the fractional delay as `phase_metric`. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.
- `P_PRESERVE_INPUT_EDGE_ORDER_AND_ASSERT`: restore: Preserve input-edge order and assert `valid` after the first emitted delayed edge. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `fractional_delay_dtc_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
