# Voltage Controlled Gain Amplifier Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `voltage_controlled_gain_amplifier.va`:
  - Module `voltage_controlled_gain_amplifier` (entry)
    - position 0: `vin_p` (input, electrical)
    - position 1: `vin_n` (input, electrical)
    - position 2: `vctrl_p` (input, electrical)
    - position 3: `vctrl_n` (input, electrical)
    - position 4: `vout` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DIFFERENTIAL_CONTROL`: restore: Use `V(vctrl_p, vctrl_n)` as the gain-control voltage. Required traces: `time`, `vctrl_p`, `vctrl_n`, `vout`.
- `P_INPUT_OFFSET_AND_GAIN`: restore: Compute the unclamped target as `1.5 * V(vctrl_p, vctrl_n) * (V(vin_p, vin_n) - 0.05) + 0.5`. Required traces: `time`, `vin_p`, `vin_n`, `vctrl_p`, `vctrl_n`, `vout`.
- `P_UNIPOLAR_OUTPUT_CLAMP`: restore: Clamp the final output target to the inclusive interval `[0.1 V, 0.9 V]`. Required traces: `time`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `voltage_controlled_gain_amplifier.va`.
Every supplied `.va` file is editable; do not add or omit files.
