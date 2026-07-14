# PAM4 Linearity Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PAM4 Linearity Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pam4_linearity_monitor.va`:
  - Module `pam4_linearity_monitor` (entry)
    - position 0: `symbol_1` (inout, electrical)
    - position 1: `symbol_0` (inout, electrical)
    - position 2: `clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `enable` (inout, electrical)
    - position 5: `level_out` (inout, electrical)
    - position 6: `linearity_metric` (inout, electrical)
    - position 7: `valid` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pam4_linearity_monitor` as `XDUT` with ordered public binding: symbol_1=symbol_1, symbol_0=symbol_0, clk=clk, rst=rst, enable=enable, level_out=level_out, linearity_metric=linearity_metric, valid=valid.

## Public Parameter Contract

- `pam4_linearity_monitor.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `pam4_linearity_monitor.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `pam4_linearity_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pam4_linearity_monitor.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `pam4_linearity_monitor.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear output, metric, and `valid`. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, decode `symbol_1..symbol_0` as one of four PAM4 levels. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.
- `P_DRIVE_LEVEL_OUT_TO_EVENLY_SPACED`: exercise and make observable: Drive `level_out` to evenly spaced voltage levels between `vss` and `vdd`. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.
- `P_EXPOSE_A_LINEARITY_METRIC_THAT_IS`: exercise and make observable: Expose a `linearity_metric` that is high only when adjacent level spacing is uniform. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.
- `P_ASSERT_VALID_AFTER_EACH_SAMPLED_SYMBOL`: exercise and make observable: Assert `valid` after each sampled symbol update. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.

The required trace names are: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
