# Supply Supervisor with Brownout POR Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `supply_supervisor_brownout_por.va`:
  - Module `supply_supervisor_brownout_por` (entry)
    - position 0: `vdd_sense` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `por_n` (output, electrical)
    - position 5: `pgood` (output, electrical)
    - position 6: `brownout` (output, electrical)
    - position 7: `delay_metric` (output, electrical)
    - position 8: `state_metric` (output, electrical)

## Public Parameter Contract

- `supply_supervisor_brownout_por.voh` defaults to `0.9` V; valid range: voh > vol; sets logic high.
- `supply_supervisor_brownout_por.vol` defaults to `0.0` V; valid range: vol < voh; sets logic low.
- `supply_supervisor_brownout_por.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `supply_supervisor_brownout_por.uvlo_rise` defaults to `0.72` V; valid range: uvlo_rise > uvlo_fall; sets brownout release threshold.
- `supply_supervisor_brownout_por.uvlo_fall` defaults to `0.64` V; valid range: uvlo_fall < uvlo_rise; sets brownout assertion threshold.
- `supply_supervisor_brownout_por.release_cycles` defaults to `4` cycles; valid range: release_cycles >= 1; sets consecutive good cycles before release.
- `supply_supervisor_brownout_por.tr` defaults to `1e-10` s; valid range: tr > 0; sets transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_SAFE`: restore: Reset or disable asserts brownout, holds POR low, clears pgood and both metrics. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.
- `P_UVLO_HYSTERESIS`: restore: Supply below uvlo_fall enters brownout and supply must exceed uvlo_rise to leave it. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.
- `P_RELEASE_DELAY`: restore: POR and pgood assert only after release_cycles consecutive good rising clock edges. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.
- `P_DIP_RESTART`: restore: A supply dip below uvlo_fall immediately reasserts brownout and clears release progress. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.
- `P_STATE_METRICS`: restore: Delay and state metrics report the saturated release count and four public supervisor states. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not use current contributions, transistor-level devices, validation logic, or simulator side channels.
- Do not hard-code evaluator stimulus timing, stop times, sample windows, or checker tolerances.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `supply_supervisor_brownout_por.va`.
Every supplied `.va` file is editable; do not add or omit files.
