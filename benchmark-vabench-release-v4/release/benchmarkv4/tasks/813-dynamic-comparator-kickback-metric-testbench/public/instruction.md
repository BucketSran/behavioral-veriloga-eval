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

Stable public Spectre binding:

The submitted `testbench.scs` must use the supplied DUT through this public binding:

- Include path: `./dut/dynamic_comparator_kickback_metric.va`
- DUT instance: `XDUT (vinp vinn clk rst enable decision kickback_metric valid) dynamic_comparator_kickback_metric`
- Required saved public traces: `vinp`, `vinn`, `clk`, `rst`, `enable`, `decision`, `kickback_metric`, `valid`
- Use one bounded transient analysis with a finite positive stop time.

You must design the stimulus yourself. Save traces as bare public signal names
(for example `clk`, not suffixed or hierarchical forms such as `clk:V` or
`XDUT.clk`). Do not redefine the DUT, drive DUT output nets, save
hierarchical/private nodes, or use checker/gold/internal files.

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


The following canonical public behavior is normative for this derived form:

- On reset or when disabled, clear `decision`, `kickback_metric`, and `valid`.
- On each enabled rising `clk` edge, latch the sign of `vinp - vinn` into `decision`.
- Drive `kickback_metric` as a voltage-coded function of the absolute input overdrive.
- Small overdrive must produce a larger kickback metric than large overdrive, up to the public rail limits.
- Assert `valid` after each completed decision update.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.


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

- 1.0+gain_step*code

- abs(v(vinp)-v(vinn))

- 0.30/(1.0+overdrive/0.030)
