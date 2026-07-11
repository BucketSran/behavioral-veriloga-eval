# Single-Shot Timer Pulse

## Task Contract

Implement `single_shot_timer_pulse.va` as a voltage-domain one-shot pulse generator for clock/timing support.

## Public Verilog-A Interface

Use this module signature:

```verilog
module single_shot_timer_pulse(vin, vout);
```

Both ports are scalar `electrical` nodes. `vin` is the voltage-coded trigger input and `vout` is the voltage-coded pulse output.

## Public Parameter Contract

- `pulse_width`: output high duration after a qualifying rising input edge, default `2n`.
- `vlogic_high`: output high level, default `0.9`.
- `vlogic_low`: output low level, default `0.0`.
- `vtrans`: rising-edge threshold for `vin`, default `0.45`.
- `tdel`: output transition delay, default `100p`.
- `trise`: output rise time, default `10p`.
- `tfall`: output fall time, default `10p`.

## Required Behavior

- Detect rising `vin` crossings at `vtrans`.
- On each qualifying rising edge, drive `vout` high after the configured transition delay.
- Use a timer to schedule the low-going state update at `edge_time + pulse_width + trise`, where `edge_time` is the qualifying rising input edge time. The voltage contribution still uses the public `tdel`, `trise`, and `tfall` transition parameters.
- Generate one output pulse per input rising edge.
- Hold the low output level between pulses.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, transistor-level devices, AC/noise analysis, checker logic, out-of-band test hooks, or simulator side channels.

## Output Contract

Return exactly one source artifact named `single_shot_timer_pulse.va`.
