# Power Mode Supply Current Metric Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Power Mode Supply Current Metric` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `power_mode_supply_current_metric.va`:
  - Module `power_mode_supply_current_metric` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `vss` (input, electrical)
    - position 2: `en` (input, electrical)
    - position 3: `pd` (input, electrical)
    - position 4: `mode` (input, electrical)
    - position 5: `load` (input, electrical)
    - position 6: `isup_metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `power_mode_supply_current_metric` as `XDUT` with ordered public binding: vdd=vdd, vss=vss, en=en, pd=pd, mode=mode, load=load, isup_metric=isup_metric.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DRIVE_ISUP_METRIC_AS_A_VOLTAGE`: exercise and make observable: Drive `isup_metric` as a voltage-coded supply-current estimate. The estimate must scale with the local supply ratio `V(vdd, vss) / vnom` clipped to the range `[0, 1.5]`. Normalize load as `V(load, vss) / vhi` clipped to `[0, 1]`. When the block is disabled or powered down, meaning `V(en) <= vth` or `V(pd) > vth`, drive `isup_metric = ipd * supply_scale`. Otherwise choose the active base metric as `iq1` when `V(mode) > vth` and `iq0` when `V(mode) <= vth`, then drive `isup_metric = (base_metric + load_gain * load_norm) * supply_scale`. The metric is not a real branch current; it is an observable behavioral macro-model output. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_BUILD_A_VOLTAGE_DOMAIN_BIAS_REFERENCE`: exercise and make observable: Build a voltage-domain bias/reference/power-management macro-model metric. The module exposes an observable supply-current demand estimate as a voltage-coded output across enable, power-down, operating mode, load demand, and local supply conditions. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: exercise and make observable: `vth = 0.45 V`: logic threshold for `en`, `pd`, and `mode`. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_VHI_0_9_V_FULL_SCALE`: exercise and make observable: `vhi = 0.9 V`: full-scale input level for `load`. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_VNOM_0_9_V_NOMINAL_SUPPLY`: exercise and make observable: `vnom = 0.9 V`: nominal supply used for supply-ratio scaling. Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.
- `P_IQ0_0_08_IQ1_0_14`: exercise and make observable: `iq0 = 0.08`, `iq1 = 0.14`: active quiescent metric levels for low and high Required traces: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.

The required trace names are: `time`, `en`, `isup_metric`, `load`, `mode`, `pd`, `vdd`, `vss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
