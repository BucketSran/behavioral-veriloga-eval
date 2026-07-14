# Rail Ramp Rate Startup Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

The repaired bundle must satisfy every public property:

- `P_RAIL_OK_ENFORCES_ENABLE_AND_SUPPLY_WINDOW`: restore: Drive rail_ok high only while enabled and the sampled local supply lies inside the public operating window. Required traces: `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `time`, `vdd`, `vss`.
- `P_RAMP_OK_QUALIFIES_STARTUP_AND_SETTLING_SLEW`: restore: Before vready, accept only positive sampled movement within dv_min..dv_max; at or above vready, accept only absolute movement no larger than dv_settle_max. Required traces: `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `time`, `vdd`, `vss`.
- `P_STARTUP_READY_REQUIRES_CONSECUTIVE_SETTLED_SAMPLES`: restore: Assert startup_ready only after ready_cycles consecutive samples satisfy rail, ramp, and vready qualification; clear the count on any invalid sample. Required traces: `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `time`, `vdd`, `vss`.
- `P_SLEW_METRIC_REPORTS_BOUNDED_DELTA`: restore: Drive slew_metric as vhi times the sampled absolute rail delta divided by dv_max, clipped to zero through one. Required traces: `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `time`, `vdd`, `vss`.
- `P_ON_EACH_RISING_CROSSING_OF_CLK`: restore: On each rising crossing of `clk`, sample `V(vdd, vss)` and compute the sampled change from the previous clock update. Drive `rail_ok` high only while `en` is high and the sampled local supply is inside the public operating window. Before the sampled rail reaches `vready`, drive `ramp_ok` high only when the sampled positive rail movement is between `dv_min` and `dv_max`. Once the sampled rail is at or above `vready`, drive `ramp_ok` high only when the absolute sampled movement is no larger than `dv_settle_max`. Accumulate consecutive settled samples only when `rail_ok` is high, `ramp_ok` is high, and the rail is at or above `vready`; clear that accumulator on any sampled invalid condition. Assert `startup_ready` only after `ready_cycles` consecutive settled updates. Drive `slew_metric` as `vhi * clip(abs(delta_v) / dv_max, 0, 1)`. Smooth the voltage-coded outputs with `transition()`. Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_BUILD_A_VOLTAGE_DOMAIN_STARTUP_MONITOR`: restore: Build a voltage-domain startup monitor for a locally supplied analog block. The module samples the local rail on a clock, checks whether the rail is inside the allowed operating window, qualifies the startup ramp rate, and releases a startup-ready flag only after the rail has settled for consecutive sampled updates. Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: restore: `vth = 0.45 V`: logic threshold for `clk` and `en`. Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_VHI_0_9_V_HIGH_LEVEL`: restore: `vhi = 0.9 V`: high level for voltage-coded outputs. Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_VDD_MIN_0_72_V_VDD`: restore: `vdd_min = 0.72 V`, `vdd_max = 1.08 V`: valid `V(vdd, vss)` operating Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.
- `P_VREADY_0_86_V_SAMPLED_RAIL`: restore: `vready = 0.86 V`: sampled rail level above which settling qualification is Required traces: `time`, `clk`, `en`, `rail_ok`, `ramp_ok`, `slew_metric`, `startup_ready`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `rail_ramp_rate_startup_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
