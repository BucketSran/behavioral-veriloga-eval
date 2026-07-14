# Current-limited Regulator Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `current_limited_regulator_macro.va`:
  - Module `current_limited_regulator_macro` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `load_demand` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `limit_metric` (output, electrical)
    - position 6: `regulation_ok` (output, electrical)

## Public Parameter Contract

- `current_limited_regulator_macro.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `current_limited_regulator_macro.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `current_limited_regulator_macro.vref` defaults to `0.75` V; valid range: vref is finite and preserves the public operating range; overrides the public vref behavior parameter consistently for this module.
- `current_limited_regulator_macro.dropout` defaults to `0.08` V; valid range: dropout is finite and preserves the public operating range; overrides the public dropout behavior parameter consistently for this module.
- `current_limited_regulator_macro.demand_limit` defaults to `0.65` V; valid range: demand_limit is finite and preserves the public operating range; overrides the public demand_limit behavior parameter consistently for this module.
- `current_limited_regulator_macro.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `current_limited_regulator_macro.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disabled operation drives vout, limit_metric, and regulation_ok low. Required traces: `time`, `vin`, `load_demand`, `enable`, `rst`, `vout`, `limit_metric`, `regulation_ok`.
- `P_NORMAL_REGULATION`: restore: With adequate headroom and sub-limit demand, vout equals vref and regulation_ok is asserted. Required traces: `time`, `vin`, `load_demand`, `enable`, `rst`, `vout`, `regulation_ok`.
- `P_DROPOUT_CLAMP`: restore: When input headroom is insufficient, vout is clamped to max(vss, vin minus dropout). Required traces: `time`, `vin`, `load_demand`, `enable`, `rst`, `vout`.
- `P_CURRENT_LIMITING`: restore: Demand above demand_limit produces limit_metric equal to the overload and reduces vout by that overload subject to rails and dropout. Required traces: `time`, `vin`, `load_demand`, `enable`, `rst`, `vout`, `limit_metric`.
- `P_REGULATION_FLAG`: restore: regulation_ok is high only for enabled, non-reset, non-limited operation with enough input headroom. Required traces: `time`, `vin`, `load_demand`, `enable`, `rst`, `regulation_ok`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavior.
- Use portable Spectre-compatible Verilog-A and voltage contributions for public outputs.
- Do not use branch-current oracles, hidden pass/fail ports, checker side channels, or testbench code in the DUT bundle.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `current_limited_regulator_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
