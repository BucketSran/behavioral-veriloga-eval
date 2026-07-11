# Binary To Thermometer Decoder 8b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bin_to_therm_8b.va`:
  - Module `bin_to_therm_8b` (entry)
    - position 0: `en` (input, electrical)
    - position 1: `b[7:0]` (input, electrical)
    - position 2: `th[255:0]` (output, electrical)

## Public Parameter Contract

- `bin_to_therm_8b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the thermometer-bus logic-high voltage.
- `bin_to_therm_8b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets en and binary-input decision thresholds.
- `bin_to_therm_8b.tr` defaults to `2e-11` s; valid range: tr > 0; sets every thermometer output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_UNSIGNED_CODE`: restore: The voltage-coded b[7:0] bus decodes as an unsigned integer from 0 through 255 with b[7] as the most significant bit. Required traces: `time`, `b[7:0]`.
- `P_DISABLED_ALL_LOW`: restore: When en is below vth, every th[255:0] output is low independent of the binary code. Required traces: `time`, `en`, `b[7:0]`, `th[255:0]`.
- `P_PREFIX_THERMOMETER`: restore: When enabled, exactly code outputs form a contiguous high prefix from th[0] through th[code-1], with all higher indices low. Required traces: `time`, `en`, `b[7:0]`, `th[255:0]`.
- `P_ENDPOINT_CODES`: restore: Enabled code 0 drives all outputs low; enabled code 255 drives th[0] through th[254] high and leaves th[255] low. Required traces: `time`, `en`, `b[7:0]`, `th[255:0]`.
- `P_LOGIC_LEVELS`: restore: High thermometer elements approach vdd and low elements approach 0 V with finite transition smoothing set by tr. Required traces: `time`, `th[255:0]`.

## Modeling Constraints

- AMS role: unary DAC element-selection decoder for data-converter support, not a generic digital utility gate.
- Use deterministic voltage-coded combinational decoding suitable for unary DAC element selection.
- Use smooth voltage contributions and compact bus iteration; do not use current contributions or transistor-level devices.
- Do not add testbench logic, validation hooks, debug ports, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bin_to_therm_8b.va`.
Every supplied `.va` file is editable; do not add or omit files.
