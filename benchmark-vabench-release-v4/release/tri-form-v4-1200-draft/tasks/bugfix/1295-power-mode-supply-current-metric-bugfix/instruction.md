# Power Mode Supply Current Metric Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `power_mode_supply_current_metric.va`:
  - Module `power_mode_supply_current_metric` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `vss` (input, electrical)
    - position 2: `en` (input, electrical)
    - position 3: `pd` (input, electrical)
    - position 4: `mode` (input, electrical)
    - position 5: `load` (input, electrical)
    - position 6: `isup_metric` (output, electrical)

## Public Parameter Contract

- `power_mode_supply_current_metric.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `power_mode_supply_current_metric.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `power_mode_supply_current_metric.vnom` defaults to `0.9`; valid range: finite; overrides vnom.
- `power_mode_supply_current_metric.iq0` defaults to `0.08`; valid range: finite; overrides iq0.
- `power_mode_supply_current_metric.iq1` defaults to `0.14`; valid range: finite; overrides iq1.
- `power_mode_supply_current_metric.ipd` defaults to `0.01`; valid range: finite; overrides ipd.
- `power_mode_supply_current_metric.load_gain` defaults to `0.20`; valid range: finite; overrides load_gain.
- `power_mode_supply_current_metric.tr` defaults to `80p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DRIVE_ISUP_METRIC_AS_A_VOLTAGE`: restore: Drive `isup_metric` as a voltage-coded supply-current estimate. The estimate must scale with the local supply ratio `V(vdd, vss) / vnom` clipped to the range `[0, 1.5]`. Normalize load as `V(load, vss) / vhi` clipped to `[0, 1]`. When the block is disabled or powered down, meaning `V(en) <= vth` or `V(pd) > vth`, drive `isup_metric = ipd * supply_scale`. Otherwise choose the active base metric as `iq1` when `V(mode) > vth` and `iq0` when `V(mode) <= vth`, then drive `isup_metric = (base_metric + load_gain * load_norm) * supply_scale`. The metric is not a real branch current; it is an observable behavioral macro-model output. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_BUILD_A_VOLTAGE_DOMAIN_BIAS_REFERENCE`: restore: Build a voltage-domain bias/reference/power-management macro-model metric. The module exposes an observable supply-current demand estimate as a voltage-coded output across enable, power-down, operating mode, load demand, and local supply conditions. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: restore: `vth = 0.45 V`: logic threshold for `en`, `pd`, and `mode`. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_VHI_0_9_V_FULL_SCALE`: restore: `vhi = 0.9 V`: full-scale input level for `load`. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_VNOM_0_9_V_NOMINAL_SUPPLY`: restore: `vnom = 0.9 V`: nominal supply used for supply-ratio scaling. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_IQ0_0_08_IQ1_0_14`: restore: `iq0 = 0.08`, `iq1 = 0.14`: active quiescent metric levels for low and high Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `power_mode_supply_current_metric.va`.
Every supplied `.va` file is editable; do not add or omit files.
