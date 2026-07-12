# Decision Router Logic Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `decision_router_logic.va`:
  - Module `decision_router_logic` (entry)
    - position 0: `vin1` (input, electrical)
    - position 1: `vin2` (input, electrical)
    - position 2: `valid` (input, electrical)
    - position 3: `x` (output, electrical)
    - position 4: `y` (output, electrical)
    - position 5: `z` (output, electrical)
    - position 6: `dm` (output, electrical)
    - position 7: `dl` (output, electrical)

## Public Parameter Contract

- `decision_router_logic.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `decision_router_logic.vh` defaults to `0.9`; valid range: finite; overrides vh.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INTERPRET_VIN1_VIN2_AND_VALID_RELATIVE`: restore: Interpret `vin1`, `vin2`, and `valid` relative to `vth`; all routed decisions below are evaluated from those voltage-coded Boolean inputs. Required traces: `time`, `dl`, `dm`, `valid`, `vin1`, `vin2`, `x`, `y`, `z`.
- `P_DRIVE_DM_HIGH_WHEN_VIN1_IS`: restore: Drive `dm` high when `vin1` is high and low otherwise. Required traces: `time`, `dl`, `dm`, `valid`, `vin1`, `vin2`, `x`, `y`, `z`.
- `P_DRIVE_DL_HIGH_WHEN_VIN1_IS`: restore: Drive `dl` high when `vin1` is low and `vin2` is high, and low otherwise. Required traces: `time`, `dl`, `dm`, `valid`, `vin1`, `vin2`, `x`, `y`, `z`.
- `P_DRIVE_X_HIGH_WHEN_VALID_IS`: restore: Drive `x` high only when `valid` is high and both decision inputs are low. Required traces: `time`, `dl`, `dm`, `valid`, `vin1`, `vin2`, `x`, `y`, `z`.
- `P_DRIVE_Y_HIGH_WHEN_VALID_IS`: restore: Drive `y` high only when `valid` is high and both decision inputs are high. Required traces: `time`, `dl`, `dm`, `valid`, `vin1`, `vin2`, `x`, `y`, `z`.
- `P_DRIVE_Z_HIGH_WHEN_VALID_IS`: restore: Drive `z` high only when `valid` is high, `vin1` is low, and `vin2` is high. Required traces: `time`, `dl`, `dm`, `valid`, `vin1`, `vin2`, `x`, `y`, `z`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `decision_router_logic.va`.
Every supplied `.va` file is editable; do not add or omit files.
