# Dynamic Comparator Kickback Metric Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Dynamic Comparator Kickback Metric` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dynamic_comparator_kickback_metric` as `XDUT` with ordered public binding: vinp=vinp, vinn=vinn, clk=clk, rst=rst, enable=enable, decision=decision, kickback_metric=kickback_metric, valid=valid.

## Public Parameter Contract

- `dynamic_comparator_kickback_metric.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `dynamic_comparator_kickback_metric.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `dynamic_comparator_kickback_metric.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `dynamic_comparator_kickback_metric.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `dynamic_comparator_kickback_metric.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear `decision`, `kickback_metric`, and `valid`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, latch the sign of `vinp - vinn` into `decision`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_DRIVE_KICKBACK_METRIC_AS_A_VOLTAGE`: exercise and make observable: Drive `kickback_metric` as a voltage-coded function of the absolute input overdrive. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_SMALL_OVERDRIVE_MUST_PRODUCE_A_LARGER`: exercise and make observable: Small overdrive must produce a larger kickback metric than large overdrive, up to the public rail limits. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_ASSERT_VALID_AFTER_EACH_COMPLETED_DECISION`: exercise and make observable: Assert `valid` after each completed decision update. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.

The required trace names are: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
