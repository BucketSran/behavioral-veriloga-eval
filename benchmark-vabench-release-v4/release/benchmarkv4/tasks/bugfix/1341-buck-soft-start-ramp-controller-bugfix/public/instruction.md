# Buck Soft-start Ramp Controller Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `buck_soft_start_ramp_controller.va`:
  - Module `buck_soft_start_ramp_controller` (entry)
    - position 0: `clk` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `target_ref` (inout, electrical)
    - position 4: `soft_ref` (inout, electrical)
    - position 5: `ramp_metric` (inout, electrical)
    - position 6: `done` (inout, electrical)

## Public Parameter Contract

- `buck_soft_start_ramp_controller.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `buck_soft_start_ramp_controller.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `buck_soft_start_ramp_controller.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `buck_soft_start_ramp_controller.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `buck_soft_start_ramp_controller.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `buck_soft_start_ramp_controller.ramp_step` defaults to `40e-3 from (0:inf)`; valid range: finite; overrides ramp_step.
- `buck_soft_start_ramp_controller.ramp_tol` defaults to `5e-3 from [0:inf)`; valid range: finite; overrides ramp_tol.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear `soft_ref`, ramp metric, and `done`. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, increase `soft_ref` toward `target_ref` by at most `ramp_step`. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.
- `P_NEVER_ALLOW_SOFT_REF_TO_EXCEED`: restore: Never allow `soft_ref` to exceed `target_ref` or the public rails. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.
- `P_EXPOSE_THE_REMAINING_RAMP_DISTANCE_ON`: restore: Expose the remaining ramp distance on `ramp_metric`. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.
- `P_ASSERT_DONE_ONLY_AFTER_SOFT_REF`: restore: Assert `done` only after `soft_ref` reaches the target within `ramp_tol`. Required traces: `time`, `clk`, `rst`, `enable`, `target_ref`, `soft_ref`, `ramp_metric`, `done`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `buck_soft_start_ramp_controller.va`.
Every supplied `.va` file is editable; do not add or omit files.
