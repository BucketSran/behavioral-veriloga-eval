# Dynamic Comparator Kickback Metric Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dynamic_comparator_kickback_metric.va`:
  - Module `dynamic_comparator_kickback_metric` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `decision` (output, electrical)
    - position 6: `kickback_metric` (output, electrical)
    - position 7: `valid` (output, electrical)

## Public Parameter Contract

- `dynamic_comparator_kickback_metric.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `dynamic_comparator_kickback_metric.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `dynamic_comparator_kickback_metric.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `dynamic_comparator_kickback_metric.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `dynamic_comparator_kickback_metric.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear `decision`, `kickback_metric`, and `valid`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, latch the sign of `vinp - vinn` into `decision`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_DRIVE_KICKBACK_METRIC_AS_A_VOLTAGE`: restore: Drive `kickback_metric` as a voltage-coded function of the absolute input overdrive. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_SMALL_OVERDRIVE_MUST_PRODUCE_A_LARGER`: restore: Small overdrive must produce a larger kickback metric than large overdrive, up to the public rail limits. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_ASSERT_VALID_AFTER_EACH_COMPLETED_DECISION`: restore: Assert `valid` after each completed decision update. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dynamic_comparator_kickback_metric.va`.
Every supplied `.va` file is editable; do not add or omit files.
