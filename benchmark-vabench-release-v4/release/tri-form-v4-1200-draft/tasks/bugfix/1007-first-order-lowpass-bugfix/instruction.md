# First Order Lowpass Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `first_order_lowpass.va`:
  - Module `first_order_lowpass` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

## Public Parameter Contract

- `first_order_lowpass.alpha` defaults to `0.025`; valid range: 0 < alpha <= 1; sets the fraction of input error applied on each update.
- `first_order_lowpass.tr` defaults to `2e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_STATE`: restore: vout begins at 0 V before the first periodic update. Required traces: `time`, `vout`.
- `P_PERIODIC_UPDATE`: restore: The internal output updates only on the public 500 ps periodic schedule using y := y + alpha*(vin-y). Required traces: `time`, `vin`, `vout`.
- `P_STEP_MONOTONICITY`: restore: For a positive input step, vout is monotone and bounded by the input level. Required traces: `time`, `vin`, `vout`.
- `P_LOW_PASS_RESPONSE`: restore: The step response is slower than an instantaneous copy of vin. Required traces: `time`, `vin`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavior with a 500 ps periodic update.
- Use voltage contributions only.
- Do not use current contributions, ddt(), idt(), undeclared artifacts, debug outputs, or validation state.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `first_order_lowpass.va`.
Every supplied `.va` file is editable; do not add or omit files.
