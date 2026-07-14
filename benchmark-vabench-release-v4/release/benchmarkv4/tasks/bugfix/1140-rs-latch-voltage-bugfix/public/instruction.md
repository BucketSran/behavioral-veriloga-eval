# RS Latch Voltage Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `rs_latch_voltage.va`:
  - Module `rs_latch_voltage` (entry)
    - position 0: `vin_s` (input, electrical)
    - position 1: `vin_r` (input, electrical)
    - position 2: `vout_q` (output, electrical)
    - position 3: `vout_qbar` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_LOGIC_THRESHOLDS_OUTPUT_AMPLITUDE`: restore: Interpret set and reset as logic high above 0.45 V and drive outputs with 0.9 V high and 0.0 V low levels. Required traces: `time`, `vin_s`, `vin_r`, `vout_q`, `vout_qbar`.
- `P_SET_RESET_PRIORITY`: restore: A set-only input drives Q high, and a reset-only input drives Q low. Required traces: `time`, `vin_s`, `vin_r`, `vout_q`, `vout_qbar`.
- `P_HOLD_STATE`: restore: When neither set-only nor reset-only is asserted, preserve the previous Q state after initializing Q low. Required traces: `time`, `vin_s`, `vin_r`, `vout_q`, `vout_qbar`.
- `P_QBAR_COMPLEMENT`: restore: Drive `vout_qbar` as the logical complement of Q. Required traces: `time`, `vout_q`, `vout_qbar`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `rs_latch_voltage.va`.
Every supplied `.va` file is editable; do not add or omit files.
