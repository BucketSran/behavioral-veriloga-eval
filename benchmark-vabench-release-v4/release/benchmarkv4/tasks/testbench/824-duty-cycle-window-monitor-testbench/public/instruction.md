# Duty-cycle Window Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Duty-cycle Window Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `duty_cycle_window_monitor.va`:
  - Module `duty_cycle_window_monitor` (entry)
    - position 0: `clk_in` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `duty_min` (inout, electrical)
    - position 4: `duty_max` (inout, electrical)
    - position 5: `duty_metric` (inout, electrical)
    - position 6: `in_window` (inout, electrical)
    - position 7: `valid` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `duty_cycle_window_monitor` as `XDUT` with ordered public binding: clk_in=clk_in, rst=rst, enable=enable, duty_min=duty_min, duty_max=duty_max, duty_metric=duty_metric, in_window=in_window, valid=valid.

## Public Parameter Contract

- `duty_cycle_window_monitor.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `duty_cycle_window_monitor.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `duty_cycle_window_monitor.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `duty_cycle_window_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `duty_cycle_window_monitor.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `duty_cycle_window_monitor.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear duty metric, window flag, and `valid`. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.
- `P_MEASURE_HIGH_AND_LOW_INTERVALS_OVER`: exercise and make observable: Measure high and low intervals over complete clock cycles using threshold crossings. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.
- `P_DRIVE_DUTY_METRIC_AS_THE_MEASURED`: exercise and make observable: Drive `duty_metric` as the measured high-time fraction mapped to the public voltage range. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.
- `P_ASSERT_IN_WINDOW_ONLY_WHEN_THE`: exercise and make observable: Assert `in_window` only when the measured duty lies between `duty_min` and `duty_max`. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.
- `P_ASSERT_VALID_AFTER_A_COMPLETE_HIGH`: exercise and make observable: Assert `valid` after a complete high/low cycle has been observed. Required traces: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.

The required trace names are: `time`, `clk_in`, `rst`, `enable`, `duty_min`, `duty_max`, `duty_metric`, `in_window`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
