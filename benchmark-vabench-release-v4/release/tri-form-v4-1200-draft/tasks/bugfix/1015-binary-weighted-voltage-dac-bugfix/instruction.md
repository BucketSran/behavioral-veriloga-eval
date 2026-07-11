# Binary Weighted Voltage DAC Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `simple_binary_voltage_dac_4b.va`:
  - Module `simple_binary_voltage_dac_4b` (entry)
    - position 0: `code_0` (input, electrical)
    - position 1: `code_1` (input, electrical)
    - position 2: `code_2` (input, electrical)
    - position 3: `code_3` (input, electrical)
    - position 4: `vref` (input, electrical)
    - position 5: `vss` (input, electrical)
    - position 6: `aout` (output, electrical)

## Public Parameter Contract

- `simple_binary_voltage_dac_4b.vth` defaults to `0.45` V; valid range: vth > 0; sets code-bit decision threshold.
- `simple_binary_voltage_dac_4b.tr` defaults to `5e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_BINARY_WEIGHTS`: restore: code_0 through code_3 form an unsigned four-bit word with weights one, two, four, and eight. Required traces: `time`, `code_0`, `code_1`, `code_2`, `code_3`, `aout`.
- `P_ENDPOINTS`: restore: Code zero maps to vss and code fifteen maps to vref. Required traces: `time`, `code_0`, `code_1`, `code_2`, `code_3`, `vref`, `vss`, `aout`.
- `P_LINEAR_MONOTONIC_MAPPING`: restore: aout changes linearly and monotonically with the unsigned code between the rail endpoints. Required traces: `time`, `code_0`, `code_1`, `code_2`, `code_3`, `vref`, `vss`, `aout`.
- `P_CONTINUOUS_UPDATE`: restore: aout responds continuously to code-bit changes without a clock event. Required traces: `time`, `code_0`, `code_1`, `code_2`, `code_3`, `aout`.

## Modeling Constraints

- Use deterministic voltage-domain continuous code mapping with finite transition smoothing.
- Use voltage contributions only.
- Do not use current contributions, ddt(), idt(), validation logic, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `simple_binary_voltage_dac_4b.va`.
Every supplied `.va` file is editable; do not add or omit files.
