# Slew Rate DAC4 Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `slew_rate_dac4.va`:
  - Module `slew_rate_dac4` (entry)
    - position 0: `d3` (input, electrical)
    - position 1: `d2` (input, electrical)
    - position 2: `d1` (input, electrical)
    - position 3: `d0` (input, electrical)
    - position 4: `vout` (output, electrical)

## Public Parameter Contract

- `slew_rate_dac4.vth` defaults to `0.45` V; valid range: vth > 0; sets the decision threshold for all voltage-coded input bits.
- `slew_rate_dac4.vref` defaults to `1` V; valid range: vref > 0; sets the full-scale analog endpoint.
- `slew_rate_dac4.slewrate` defaults to `100000000` V/s; valid range: slewrate > 0; sets the maximum positive and negative magnitude of dvout/dt.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_BINARY_MAPPING`: restore: d3 is the MSB and d0 is the LSB of an unsigned four-bit code whose target output is binary weighted. Required traces: `time`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_ENDPOINTS`: restore: Code 0 targets 0 V and code 15 targets vref. Required traces: `time`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_CODE_MONOTONICITY`: restore: A larger stable input code does not produce a lower settled output voltage. Required traces: `time`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_SLEW_LIMIT`: restore: During a target change, the magnitude of the output slope does not exceed slewrate. Required traces: `time`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_SETTLED_TARGET`: restore: After sufficient time at a stable code, vout reaches the corresponding code-to-vref target. Required traces: `time`, `d3`, `d2`, `d1`, `d0`, `vout`.

## Modeling Constraints

- Use deterministic continuous voltage-domain DAC behavior.
- Use the Verilog-A slew() operator for symmetric slew limiting.
- Do not hard-code stimulus timing or add current contributions, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `slew_rate_dac4.va`.
Every supplied `.va` file is editable; do not add or omit files.
