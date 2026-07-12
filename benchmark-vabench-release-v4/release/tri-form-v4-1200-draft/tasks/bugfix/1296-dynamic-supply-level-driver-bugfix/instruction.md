# Dynamic Supply Level Driver Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dynamic_supply_level_driver.va`:
  - Module `dynamic_supply_level_driver` (entry)
    - position 0: `din` (input, electrical)
    - position 1: `vdd` (input, electrical)
    - position 2: `vss` (input, electrical)
    - position 3: `out` (output, electrical)

## Public Parameter Contract

- `dynamic_supply_level_driver.vsup_min` defaults to `0.55`; valid range: finite; overrides vsup_min.
- `dynamic_supply_level_driver.vth_frac` defaults to `0.5`; valid range: finite; overrides vth_frac.
- `dynamic_supply_level_driver.vlo_frac` defaults to `0.0`; valid range: finite; overrides vlo_frac.
- `dynamic_supply_level_driver.vhi_frac` defaults to `1.0`; valid range: finite; overrides vhi_frac.
- `dynamic_supply_level_driver.tr` defaults to `40p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_MODEL_A_DYNAMIC_SUPPLY_ELECTRICAL_LEVEL`: restore: Model a dynamic-supply electrical level driver. Compute the input level relative to the local rails, not global ground. When `V(vdd, vss)` is at least `vsup_min`, drive `out` to the local low or high rail-derived level according to whether the normalized input exceeds `vth_frac`. When the supply is below `vsup_min`, drive `out` to the local low level. Smooth the output with `transition()`. Required traces: `time`, `din`, `out`, `vdd`, `vss`.
- `P_BUILD_A_DYNAMIC_SUPPLY_VOLTAGE_DOMAIN`: restore: Build a dynamic-supply voltage-domain level driver. The module thresholds its input relative to local supply rails, drives its output relative to those same rails, and falls back to the local low level when the supply is invalid. Required traces: `time`, `din`, `out`, `vdd`, `vss`.
- `P_VSUP_MIN_0_55_V_MINIMUM`: restore: `vsup_min = 0.55 V`: minimum `V(vdd, vss)` required for normal operation. Required traces: `time`, `din`, `out`, `vdd`, `vss`.
- `P_VTH_FRAC_0_5_INPUT_THRESHOLD`: restore: `vth_frac = 0.5`: input threshold expressed as a fraction of the local supply Required traces: `time`, `din`, `out`, `vdd`, `vss`.
- `P_VLO_FRAC_0_0_VHI_FRAC`: restore: `vlo_frac = 0.0`, `vhi_frac = 1.0`: output low and high levels expressed as Required traces: `time`, `din`, `out`, `vdd`, `vss`.
- `P_TR_40P_OUTPUT_TRANSITION_SMOOTHING_TIME`: restore: `tr = 40p`: output transition smoothing time. Required traces: `time`, `din`, `out`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dynamic_supply_level_driver.va`.
Every supplied `.va` file is editable; do not add or omit files.
