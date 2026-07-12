# Analog Mux Threshold Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `analog_mux_threshold.va`:
  - Module `analog_mux_threshold` (entry)
    - position 0: `vin1` (input, electrical)
    - position 1: `vin2` (input, electrical)
    - position 2: `vsel` (input, electrical)
    - position 3: `vout` (output, electrical)

## Public Parameter Contract

- `analog_mux_threshold.vth` defaults to `0.45` V; valid range: finite real value; sets the select threshold used for initial selection and subsequent threshold crossings.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_HIGH_SELECTS_VIN1`: restore: When vsel is above vth, vout follows vin1 rather than vin2. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.
- `P_LOW_SELECTS_VIN2`: restore: When vsel is at or below vth, vout follows vin2 rather than vin1. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.
- `P_BIDIRECTIONAL_SELECTION`: restore: The selected input updates after both rising and falling crossings of vsel through vth. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.
- `P_INITIAL_SELECTION`: restore: Before any select transition, vout is selected from the initial vsel level using the same strict-greater-than threshold rule. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.
- `P_NO_MIXING`: restore: The output represents one selected input and does not average or sum vin1 and vin2. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain threshold selection.
- Respond to both select directions and establish selection at simulation start.
- Do not add input mixing, unrelated retained state, current contributions, or validation-only hooks.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `analog_mux_threshold.va`.
Every supplied `.va` file is editable; do not add or omit files.
