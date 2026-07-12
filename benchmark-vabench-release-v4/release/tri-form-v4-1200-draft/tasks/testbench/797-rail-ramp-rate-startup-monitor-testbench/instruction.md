# Rail Ramp Rate Startup Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Rail Ramp Rate Startup Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `rail_ramp_rate_startup_monitor.va`:
  - Module `rail_ramp_rate_startup_monitor` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vdd` (input, electrical)
    - position 2: `vss` (input, electrical)
    - position 3: `en` (input, electrical)
    - position 4: `rail_ok` (output, electrical)
    - position 5: `ramp_ok` (output, electrical)
    - position 6: `startup_ready` (output, electrical)
    - position 7: `slew_metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `rail_ramp_rate_startup_monitor` as `XDUT` with ordered public binding: clk=clk, vdd=vdd, vss=vss, en=en, rail_ok=rail_ok, ramp_ok=ramp_ok, startup_ready=startup_ready, slew_metric=slew_metric.

## Public Parameter Contract

- `rail_ramp_rate_startup_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `rail_ramp_rate_startup_monitor.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `rail_ramp_rate_startup_monitor.vdd_min` defaults to `0.72`; valid range: finite; overrides vdd_min.
- `rail_ramp_rate_startup_monitor.vdd_max` defaults to `1.08`; valid range: finite; overrides vdd_max.
- `rail_ramp_rate_startup_monitor.vready` defaults to `0.86`; valid range: finite; overrides vready.
- `rail_ramp_rate_startup_monitor.dv_min` defaults to `0.025`; valid range: finite; overrides dv_min.
- `rail_ramp_rate_startup_monitor.dv_max` defaults to `0.20`; valid range: finite; overrides dv_max.
- `rail_ramp_rate_startup_monitor.dv_settle_max` defaults to `0.030`; valid range: finite; overrides dv_settle_max.
- `rail_ramp_rate_startup_monitor.ready_cycles` defaults to `3`; valid range: finite; overrides ready_cycles.
- `rail_ramp_rate_startup_monitor.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RAIL_OK_ENFORCES_ENABLE_AND_SUPPLY_WINDOW`: exercise and make observable: Drive rail_ok high only while enabled and the sampled local supply lies inside the public operating window. Required traces: `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `time`, `vdd`, `vss`.
- `P_RAMP_OK_QUALIFIES_STARTUP_AND_SETTLING_SLEW`: exercise and make observable: Before vready, accept only positive sampled movement within dv_min..dv_max; at or above vready, accept only absolute movement no larger than dv_settle_max. Required traces: `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `time`, `vdd`, `vss`.
- `P_STARTUP_READY_REQUIRES_CONSECUTIVE_SETTLED_SAMPLES`: exercise and make observable: Assert startup_ready only after ready_cycles consecutive samples satisfy rail, ramp, and vready qualification; clear the count on any invalid sample. Required traces: `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `time`, `vdd`, `vss`.
- `P_SLEW_METRIC_REPORTS_BOUNDED_DELTA`: exercise and make observable: Drive slew_metric as vhi times the sampled absolute rail delta divided by dv_max, clipped to zero through one. Required traces: `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `time`, `vdd`, `vss`.
- `P_ON_EACH_RISING_CROSSING_OF_CLK`: exercise and make observable: On each rising crossing of `clk`, sample `V(vdd, vss)` and compute the sampled change from the previous clock update. Drive `rail_ok` high only while `en` is high and the sampled local supply is inside the public operating window. Before the sampled rail reaches `vready`, drive `ramp_ok` high only when the sampled positive rail movement is between `dv_min` and `dv_max`. Once the sampled rail is at or above `vready`, drive `ramp_ok` high only when the absolute sampled movement is no larger than `dv_settle_max`. Accumulate consecutive settled samples only when `rail_ok` is high, `ramp_ok` is high, and the rail is at or above `vready`; clear that accumulator on any sampled invalid condition. Assert `startup_ready` only after `ready_cycles` consecutive settled updates. Drive `slew_metric` as `vhi * clip(abs(delta_v) / dv_max, 0, 1)`. Smooth the voltage-coded outputs with `transition()`. Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_BUILD_A_VOLTAGE_DOMAIN_STARTUP_MONITOR`: exercise and make observable: Build a voltage-domain startup monitor for a locally supplied analog block. The module samples the local rail on a clock, checks whether the rail is inside the allowed operating window, qualifies the startup ramp rate, and releases a startup-ready flag only after the rail has settled for consecutive sampled updates. Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: exercise and make observable: `vth = 0.45 V`: logic threshold for `clk` and `en`. Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_VHI_0_9_V_HIGH_LEVEL`: exercise and make observable: `vhi = 0.9 V`: high level for voltage-coded outputs. Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_VDD_MIN_0_72_V_VDD`: exercise and make observable: `vdd_min = 0.72 V`, `vdd_max = 1.08 V`: valid `V(vdd, vss)` operating Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_VREADY_0_86_V_SAMPLED_RAIL`: exercise and make observable: `vready = 0.86 V`: sampled rail level above which settling qualification is Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.

The required trace names are: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
