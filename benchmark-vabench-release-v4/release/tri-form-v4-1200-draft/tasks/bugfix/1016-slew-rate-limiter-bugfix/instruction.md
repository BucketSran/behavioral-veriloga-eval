# Slew Rate Limiter Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `slew_rate_limiter.va`:
  - Module `slew_rate_limiter` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

## Public Parameter Contract

- `slew_rate_limiter.step` defaults to `0.015` V; valid range: step > 0; sets maximum state change per update.
- `slew_rate_limiter.tr` defaults to `2e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_ZERO`: restore: vout begins at 0 V. Required traces: `time`, `vout`.
- `P_PERIODIC_UPDATE`: restore: The state changes only on the public 1 ns periodic update schedule. Required traces: `time`, `vin`, `vout`.
- `P_BIDIRECTIONAL_STEP_LIMIT`: restore: Each rising or falling update changes the state toward vin by no more than step. Required traces: `time`, `vin`, `vout`.
- `P_NEAR_TARGET_SETTLE`: restore: When vin is within one step, vout may settle directly to vin. Required traces: `time`, `vin`, `vout`.
- `P_EVENTUAL_TRACKING`: restore: The limited response eventually reaches sustained high and low input levels while remaining non-instantaneous. Required traces: `time`, `vin`, `vout`.

## Modeling Constraints

- Use deterministic 1 ns timer-updated voltage-domain behavior.
- Use voltage contributions only.
- Do not use current contributions, ddt(), idt(), undeclared state outputs, or validation hooks.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `slew_rate_limiter.va`.
Every supplied `.va` file is editable; do not add or omit files.
