# Dual Track Sample Hold

## Task Contract
Implement `dual_track_sample_hold.va`, a voltage-domain dual complementary track/hold DUT. This is a sampling/analog-memory L1 component, not a standalone L2 flow.

## Public Verilog-A Interface
Declare module `dual_track_sample_hold(vdd, vss, clk, vin, vout, phase)` with scalar electrical ports. `vdd` and `vss` are local rails, `clk` is the voltage-coded phase control, `vin` is the sampled analog input, `vout` is the held output, and `phase` is high while the output stage tracks.

## Public Parameter Contract
Provide overrideable public parameters:

- `vth = 0.45 V`: clock threshold.
- `tick = 0.5 ns from (0:inf)`: behavioral update interval.
- `alpha_in = 0.45 from (0:1]`: input-stage tracking fraction per update.
- `alpha_out = 0.55 from (0:1]`: output-stage tracking fraction per update.
- `tedge = 50 ps from (0:inf)`: output smoothing time.
- `vinit = 0.0 V`: initial stored value.

## Required Behavior
During low clock phase, the input stage tracks `vin` with finite acquisition while the output stage holds. On the rising clock transition, the input stage retains its acquired value. During high clock phase, the output stage tracks that retained input-stage value with finite bandwidth. On falling clock transition, the output stage holds until the next high phase. Clamp internal stored voltages to the local rail span and drive `phase` high only during output-stage tracking.

## Modeling Constraints
Use voltage contributions and smooth voltage-domain transitions. Do not emit a Spectre testbench, checker logic, out-of-band test hooks, current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Output Contract
Return exactly one source artifact named `dual_track_sample_hold.va`.
