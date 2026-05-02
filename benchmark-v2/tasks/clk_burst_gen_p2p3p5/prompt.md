# Task: gated_event_passer

Design a Verilog-A module named `gated_event_passer` that implements a module which periodically allows the first N events of an input event stream to appear on the output, then suppresses all remaining events until the cycle resets.

## Module Interface

The module shall have the following ports:
- `event_in` (input, electrical): the input event stream signal.
- `clear_n` (input, electrical, active-low): asynchronous reset. When low, the internal counter resets and the output is forced low.
- `burst_out` (output, electrical): the output signal that reproduces selected events from the input.

## Behavioral Specification

1. **Event Counting Cycle**: The module operates in repeating cycles of 6 input events. Each cycle works as follows:
   - The module detects rising edges of `event_in` (using a threshold voltage `vth`).
   - On each rising edge, the module increments an internal counter.
   - The counter wraps from 5 back to 0, completing one full cycle every 6 rising edges.

2. **Output Enable Window**: Within each cycle of 6 events, the output `burst_out` is enabled for only the first 2 rising edges. During this enabled window, the output follows the high/low state of `event_in` (i.e., when `event_in` is above `vth`, the output drives `vdd`; when below, the output drives 0). For the remaining 4 events in the cycle, the output is suppressed and stays at 0 regardless of `event_in`.

3. **Reset Behavior**: When `clear_n` is below `vth` (logic low), the internal counter resets to 0, the output enable state resets, and `burst_out` is forced to 0. When `clear_n` returns high, a new cycle begins from event count 0 (the first two events of the new cycle will be passed to the output).

4. **Output Driver**: Use the `transition()` filter when driving `burst_out` with a default transition time of `30p`.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `div`     | `6`     | Number of input events per full cycle |
| `vdd`     | `1.2`   | Output high voltage level |
| `vth`     | `0.6`   | Input threshold voltage for detecting logic high/low |

## Constraints

- Use the standard `disciplines.vams` and `constants.vams` includes.
- Use `@(cross(...))` for edge detection.
- Do NOT use any `@(timer)` or `$random` constructs.
- The output must use the `transition()` analog filter.

---

## Public Evaluation Contract

The design will be verified using the following Spectre testbench. Ensure your DUT matches the port names, parameter names, and simulation settings defined here.

```spectre
simulator lang=spectre
global 0
ahdl_include "gated_event_passer.va"
Vevent_in (event_in 0) vsource type=pulse val0=0 val1=1.2 period=50n width=25n rise=1n fall=1n
Vclear_n (clear_n 0) vsource type=pwl wave=[0 0 115n 0 117n 1.2 2000n 1.2]
IDUT (event_in clear_n burst_out) gated_event_passer div=6 vdd=1.2 vth=0.6
tran tran stop=2000n maxstep=5n
save event_in clear_n burst_out
```

The expected output behavior:
- `burst_out` should be low during reset (before ~117ns).
- After `clear_n` goes high, `burst_out` should show groups of 1-2 pulses followed by quiet intervals, repeating with a period of approximately 300ns (6 events * 50ns per event).
- Within each active group, `burst_out` pulses should match the timing of `event_in` pulses.
