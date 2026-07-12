# Non-overlapping Clock Generator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Non-overlapping Clock Generator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `nonoverlap_clock_generator.va`:
  - Module `nonoverlap_clock_generator` (entry)
    - position 0: `clk_in` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `phi1` (output, electrical)
    - position 4: `phi2` (output, electrical)
    - position 5: `deadtime_metric` (output, electrical)
    - position 6: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `nonoverlap_clock_generator` as `XDUT` with ordered public binding: clk_in=clk_in, rst=rst, enable=enable, phi1=phi1, phi2=phi2, deadtime_metric=deadtime_metric, valid=valid.

## Public Parameter Contract

- `nonoverlap_clock_generator.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `nonoverlap_clock_generator.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `nonoverlap_clock_generator.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `nonoverlap_clock_generator.dead_ticks` defaults to `5 from [1:100]`; valid range: finite; overrides dead_ticks.
- `nonoverlap_clock_generator.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.
- `nonoverlap_clock_generator.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_OR_A_LOW_ENABLE_CLEARS`: exercise and make observable: Reset or a low `enable` clears both phases, `deadtime_metric`, and `valid`. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_A_RISING_CLK_IN_REQUEST_EVENTUALLY`: exercise and make observable: A rising `clk_in` request eventually enables `phi1`; a falling `clk_in` request eventually enables `phi2`. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_DURING_EACH_HANDOFF_BOTH_PHI1_AND`: exercise and make observable: During each handoff, both `phi1` and `phi2` remain low for the configured dead-time interval. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_PHI1_AND_PHI2_MUST_NEVER_BE`: exercise and make observable: `phi1` and `phi2` must never be high at the same time. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_DEADTIME_METRIC_IS_HIGH_ONLY_WHILE`: exercise and make observable: `deadtime_metric` is high only while a pending phase request is in the enforced both-low interval. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_VALID_BECOMES_HIGH_AFTER_THE_FIRST`: exercise and make observable: `valid` becomes high after the first enabled handoff completes and remains high until reset or disable. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.

The required trace names are: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
