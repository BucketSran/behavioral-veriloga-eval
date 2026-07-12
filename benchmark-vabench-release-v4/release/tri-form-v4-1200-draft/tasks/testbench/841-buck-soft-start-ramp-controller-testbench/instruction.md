# Buck Soft-start Ramp Controller Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Buck Soft-start Ramp Controller` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `buck_soft_start_ramp_controller.va`:
  - Module `buck_soft_start_ramp_controller` (entry)
    - position 0: `clk` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `target_ref` (inout, electrical)
    - position 4: `soft_ref` (inout, electrical)
    - position 5: `ramp_metric` (inout, electrical)
    - position 6: `done` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `buck_soft_start_ramp_controller` as `XDUT` with ordered public binding: clk=clk, rst=rst, enable=enable, target_ref=target_ref, soft_ref=soft_ref, ramp_metric=ramp_metric, done=done.

## Public Parameter Contract

- `buck_soft_start_ramp_controller.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `buck_soft_start_ramp_controller.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `buck_soft_start_ramp_controller.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `buck_soft_start_ramp_controller.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `buck_soft_start_ramp_controller.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `buck_soft_start_ramp_controller.ramp_step` defaults to `40e-3 from (0:inf)`; valid range: finite; overrides ramp_step.
- `buck_soft_start_ramp_controller.ramp_tol` defaults to `5e-3 from [0:inf)`; valid range: finite; overrides ramp_tol.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear `soft_ref`, ramp metric, and `done`. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, increase `soft_ref` toward `target_ref` by at most `ramp_step`. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.
- `P_NEVER_ALLOW_SOFT_REF_TO_EXCEED`: exercise and make observable: Never allow `soft_ref` to exceed `target_ref` or the public rails. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.
- `P_EXPOSE_THE_REMAINING_RAMP_DISTANCE_ON`: exercise and make observable: Expose the remaining ramp distance on `ramp_metric`. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.
- `P_ASSERT_DONE_ONLY_AFTER_SOFT_REF`: exercise and make observable: Assert `done` only after `soft_ref` reaches the target within `ramp_tol`. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.

The required trace names are: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
