# Supply Supervisor with Brownout POR Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Supply Supervisor with Brownout POR` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `supply_supervisor_brownout_por` as `XDUT` with ordered public binding: vdd_sense=vdd_sense, clk=clk, rst=rst, enable=enable, por_n=por_n, pgood=pgood, brownout=brownout, delay_metric=delay_metric, state_metric=state_metric.

## Public Parameter Contract

- `supply_supervisor_brownout_por.voh` defaults to `0.9` V; valid range: voh > vol; sets logic high.
- `supply_supervisor_brownout_por.vol` defaults to `0.0` V; valid range: vol < voh; sets logic low.
- `supply_supervisor_brownout_por.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `supply_supervisor_brownout_por.uvlo_rise` defaults to `0.72` V; valid range: uvlo_rise > uvlo_fall; sets brownout release threshold.
- `supply_supervisor_brownout_por.uvlo_fall` defaults to `0.64` V; valid range: uvlo_fall < uvlo_rise; sets brownout assertion threshold.
- `supply_supervisor_brownout_por.release_cycles` defaults to `4` cycles; valid range: release_cycles >= 1; sets consecutive good cycles before release.
- `supply_supervisor_brownout_por.tr` defaults to `1e-10` s; valid range: tr > 0; sets transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_DISABLE_SAFE`: exercise and make observable: Reset or disable asserts brownout, holds POR low, clears pgood and both metrics. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.
- `P_UVLO_HYSTERESIS`: exercise and make observable: Supply below uvlo_fall enters brownout and supply must exceed uvlo_rise to leave it. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.
- `P_RELEASE_DELAY`: exercise and make observable: POR and pgood assert only after release_cycles consecutive good rising clock edges. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.
- `P_DIP_RESTART`: exercise and make observable: A supply dip below uvlo_fall immediately reasserts brownout and clears release progress. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.
- `P_STATE_METRICS`: exercise and make observable: Delay and state metrics report the saturated release count and four public supervisor states. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.

The required trace names are: `time`, `vdd_sense`, `clk`, `rst`, `enable`, `por_n`, `pgood`, `brownout`, `delay_metric`, `state_metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
