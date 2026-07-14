# Reference Settling Window Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Reference Settling Window Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `reference_settling_window_monitor.va`:
  - Module `reference_settling_window_monitor` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `ref` (input, electrical)
    - position 3: `target` (input, electrical)
    - position 4: `valid` (output, electrical)
    - position 5: `err_metric` (output, electrical)
    - position 6: `settle_mon` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `reference_settling_window_monitor` as `XDUT` with ordered public binding: clk=clk, rst=rst, ref=ref, target=target, valid=valid, err_metric=err_metric, settle_mon=settle_mon.

## Public Parameter Contract

- `reference_settling_window_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `reference_settling_window_monitor.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `reference_settling_window_monitor.tol` defaults to `0.035`; valid range: finite; overrides tol.
- `reference_settling_window_monitor.err_scale` defaults to `0.20`; valid range: finite; overrides err_scale.
- `reference_settling_window_monitor.settle_cycles` defaults to `3`; valid range: finite; overrides settle_cycles.
- `reference_settling_window_monitor.tr` defaults to `80p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_EACH_RISING_CROSSING_OF_CLK`: exercise and make observable: On each rising crossing of `clk`, measure the absolute difference between `ref` and `target`. Drive `err_metric` as the clipped error magnitude scaled by `err_scale`. While reset is high, clear the settling counter and keep `valid` low. Otherwise, increment the counter on each in-window sample, clear it on any out-of-window sample, and assert `valid` only after `settle_cycles` consecutive in-window samples. Drive `settle_mon` as bounded progress from 0 to `vhi`. Smooth all outputs with `transition()`. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_BUILD_A_MEASUREMENT_STYLE_BIAS_REFERENCE`: exercise and make observable: Build a measurement-style bias/reference monitor. The module samples a reference voltage against a target, reports the bounded error magnitude, and asserts validity only after consecutive in-window samples. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: exercise and make observable: `vth = 0.45 V`: logic threshold for `clk` and `rst`. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_VHI_0_9_V_HIGH_LEVEL`: exercise and make observable: `vhi = 0.9 V`: high level for voltage-coded outputs. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_TOL_0_035_V_ALLOWED_ABSOLUTE`: exercise and make observable: `tol = 0.035 V`: allowed absolute error around `target`. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.
- `P_ERR_SCALE_0_20_V_ERROR`: exercise and make observable: `err_scale = 0.20 V`: error that maps to full-scale `err_metric`. Required traces: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.

The required trace names are: `time`, `clk`, `err_metric`, `ref`, `rst`, `settle_mon`, `target`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
