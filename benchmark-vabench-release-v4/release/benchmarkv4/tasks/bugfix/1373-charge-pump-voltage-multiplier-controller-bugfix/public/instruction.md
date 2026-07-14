# Charge-pump Voltage Multiplier Controller Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `phase_generator.va`:
  - Module `phase_generator` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `phase_a` (output, electrical)
    - position 4: `phase_b` (output, electrical)
    - position 5: `phase_tick` (output, electrical)
- Artifact `pump_stage_model.va`:
  - Module `pump_stage_model` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `phase_a` (input, electrical)
    - position 4: `phase_b` (input, electrical)
    - position 5: `pump_en` (input, electrical)
    - position 6: `vout` (output, electrical)
- Artifact `regulation_comparator.va`:
  - Module `regulation_comparator` (required_submodule)
    - position 0: `vout` (input, electrical)
    - position 1: `target` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `pump_en` (output, electrical)
    - position 5: `regulation_error` (output, electrical)
- Artifact `voltage_multiplier_top.va`:
  - Module `voltage_multiplier_top` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `target` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `phase_a` (output, electrical)
    - position 6: `phase_b` (output, electrical)
    - position 7: `pump_en` (output, electrical)
    - position 8: `regulation_error` (output, electrical)
    - position 9: `ready` (output, electrical)

## Public Parameter Contract

- `phase_generator.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `phase_generator.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `phase_generator.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `phase_generator.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `pump_stage_model.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `pump_stage_model.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `pump_stage_model.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `pump_stage_model.pump_step` defaults to `0.04` V; valid range: pump_step is finite and preserves the public operating range; overrides the public pump_step behavior parameter consistently for this module.
- `pump_stage_model.leak_step` defaults to `0.005` V; valid range: leak_step is finite and preserves the public operating range; overrides the public leak_step behavior parameter consistently for this module.
- `pump_stage_model.vout_max` defaults to `1.8` V; valid range: vout_max is finite and preserves the public operating range; overrides the public vout_max behavior parameter consistently for this module.
- `pump_stage_model.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `regulation_comparator.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `regulation_comparator.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `regulation_comparator.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `regulation_comparator.ready_tol` defaults to `0.025` V; valid range: ready_tol is finite and preserves the public operating range; overrides the public ready_tol behavior parameter consistently for this module.
- `regulation_comparator.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `voltage_multiplier_top.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `voltage_multiplier_top.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `voltage_multiplier_top.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `voltage_multiplier_top.pump_step` defaults to `0.04` V; valid range: pump_step is finite and preserves the public operating range; overrides the public pump_step behavior parameter consistently for this module.
- `voltage_multiplier_top.leak_step` defaults to `0.005` V; valid range: leak_step is finite and preserves the public operating range; overrides the public leak_step behavior parameter consistently for this module.
- `voltage_multiplier_top.ready_tol` defaults to `0.025` V; valid range: ready_tol is finite and preserves the public operating range; overrides the public ready_tol behavior parameter consistently for this module.
- `voltage_multiplier_top.vout_max` defaults to `1.8` V; valid range: vout_max is finite and preserves the public operating range; overrides the public vout_max behavior parameter consistently for this module.
- `voltage_multiplier_top.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset clears vout, pump control, readiness, and regulation state; disabled operation suppresses pumping. Required traces: `time`, `clk`, `rst`, `enable`, `vout`, `pump_en`, `regulation_error`, `ready`.
- `P_NONOVERLAP_PHASES`: restore: Enabled clock updates alternate phase_a and phase_b while never asserting both phases together. Required traces: `time`, `clk`, `rst`, `enable`, `phase_a`, `phase_b`.
- `P_PUMP_REGULATION`: restore: While pump_en is active, enabled phase updates raise vout in bounded pump steps; without pumping, vout leaks downward and remains within rails. Required traces: `time`, `clk`, `rst`, `enable`, `target`, `phase_a`, `phase_b`, `pump_en`, `vout`.
- `P_ERROR_REPORTING`: restore: regulation_error continuously reports target minus vout and pump_en requests pumping below the lower tolerance boundary. Required traces: `time`, `rst`, `enable`, `target`, `vout`, `pump_en`, `regulation_error`.
- `P_READY_QUALIFICATION`: restore: Ready asserts only after three consecutive enabled clock updates within the regulation tolerance and clears outside qualification. Required traces: `time`, `clk`, `rst`, `enable`, `regulation_error`, `ready`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavior.
- Use portable Spectre-compatible Verilog-A and voltage contributions for public outputs.
- Do not use branch-current oracles, hidden pass/fail ports, checker side channels, or testbench code in the DUT bundle.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `phase_generator.va`, `pump_stage_model.va`, `regulation_comparator.va`, `voltage_multiplier_top.va`.
Every supplied `.va` file is editable; do not add or omit files.
