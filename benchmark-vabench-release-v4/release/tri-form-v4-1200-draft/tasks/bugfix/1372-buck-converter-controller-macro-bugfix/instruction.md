# Buck Converter Controller Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `buck_ctrl_top.va`:
  - Module `buck_ctrl_top` (entry)
    - position 0: `vfb` (input, electrical)
    - position 1: `vref` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `pwm` (output, electrical)
    - position 6: `duty_metric` (output, electrical)
    - position 7: `soft_ref` (output, electrical)
    - position 8: `pgood` (output, electrical)
- Artifact `error_comparator.va`:
  - Module `error_comparator` (required_submodule)
    - position 0: `vfb` (input, electrical)
    - position 1: `soft_ref` (input, electrical)
    - position 2: `duty_up` (output, electrical)
- Artifact `power_good.va`:
  - Module `power_good` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `vfb` (input, electrical)
    - position 4: `vref` (input, electrical)
    - position 5: `pgood` (output, electrical)
- Artifact `pwm_modulator.va`:
  - Module `pwm_modulator` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `duty_up` (input, electrical)
    - position 4: `pwm` (output, electrical)
    - position 5: `duty_metric` (output, electrical)
- Artifact `soft_start.va`:
  - Module `soft_start` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `vref` (input, electrical)
    - position 4: `soft_ref` (output, electrical)

## Public Parameter Contract

- `buck_ctrl_top.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `buck_ctrl_top.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `buck_ctrl_top.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `buck_ctrl_top.duty_min` defaults to `0.05`; valid range: 0 <= duty_min < duty_max; overrides the public duty_min behavior parameter consistently for this module.
- `buck_ctrl_top.duty_max` defaults to `0.95`; valid range: duty_min < duty_max <= 1; overrides the public duty_max behavior parameter consistently for this module.
- `buck_ctrl_top.soft_step` defaults to `0.025` V; valid range: soft_step is finite and preserves the public operating range; overrides the public soft_step behavior parameter consistently for this module.
- `buck_ctrl_top.pgood_tol` defaults to `0.025` V; valid range: pgood_tol is finite and preserves the public operating range; overrides the public pgood_tol behavior parameter consistently for this module.
- `buck_ctrl_top.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `error_comparator.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `error_comparator.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `error_comparator.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `power_good.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `power_good.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `power_good.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `power_good.pgood_tol` defaults to `0.025` V; valid range: pgood_tol is finite and preserves the public operating range; overrides the public pgood_tol behavior parameter consistently for this module.
- `power_good.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `pwm_modulator.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `pwm_modulator.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `pwm_modulator.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `pwm_modulator.duty_min` defaults to `0.05`; valid range: 0 <= duty_min < duty_max; overrides the public duty_min behavior parameter consistently for this module.
- `pwm_modulator.duty_max` defaults to `0.95`; valid range: duty_min < duty_max <= 1; overrides the public duty_max behavior parameter consistently for this module.
- `pwm_modulator.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `soft_start.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `soft_start.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `soft_start.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `soft_start.soft_step` defaults to `0.025` V; valid range: soft_step is finite and preserves the public operating range; overrides the public soft_step behavior parameter consistently for this module.
- `soft_start.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disabled operation clears PWM, duty metric, soft reference, and power-good. Required traces: `time`, `clk`, `rst`, `enable`, `pwm`, `duty_metric`, `soft_ref`, `pgood`.
- `P_SOFT_START_TRACKING`: restore: At enabled rising clock edges soft_ref moves toward vref by the configured soft-step and never overshoots the target. Required traces: `time`, `clk`, `rst`, `enable`, `vref`, `soft_ref`.
- `P_DUTY_DIRECTION_BOUNDS`: restore: The duty metric increases when vfb is below soft_ref, decreases otherwise, and remains within the configured duty bounds. Required traces: `time`, `clk`, `rst`, `enable`, `vfb`, `soft_ref`, `duty_metric`.
- `P_PWM_ENCODING`: restore: PWM high samples are rail-valid and their enabled-cycle activity is consistent with a nonzero bounded duty command. Required traces: `time`, `clk`, `rst`, `enable`, `pwm`, `duty_metric`.
- `P_POWER_GOOD_QUALIFICATION`: restore: Power-good asserts only after three consecutive enabled clock updates with vfb within pgood_tol of vref and clears when qualification is lost. Required traces: `time`, `clk`, `rst`, `enable`, `vfb`, `vref`, `pgood`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavior.
- Use portable Spectre-compatible Verilog-A and voltage contributions for public outputs.
- Do not use branch-current oracles, hidden pass/fail ports, checker side channels, or testbench code in the DUT bundle.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `buck_ctrl_top.va`, `error_comparator.va`, `power_good.va`, `pwm_modulator.va`, `soft_start.va`.
Every supplied `.va` file is editable; do not add or omit files.
