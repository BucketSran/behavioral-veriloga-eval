# Task: charge_pump

Design a Verilog-A module named `charge_pump` that integrates digital UP/DN pulse signals onto an analog control voltage node. Each rising edge of a lead pulse increases the output by a fixed step; each rising edge of a lag pulse decreases the output by the same step.

## Module Interface

| Port | Direction | Description |
|------|-----------|-------------|
| vdd | inout | Positive supply |
| vss | inout | Ground |
| lead_pulse | input | Lead pulse input: rising edge increases pump_out |
| lag_pulse | input | Lag pulse input: rising edge decreases pump_out |
| pump_out | output | Integrated control voltage |

## Behavioral Specification

1. The output `pump_out` starts at mid-supply: (V(vdd) + V(vss)) / 2.
2. On each rising edge of `lead_pulse` (voltage crosses the logic threshold upward), `pump_out` increases by `charge_step` volts. The output must not exceed V(vdd).
3. On each rising edge of `lag_pulse`, `pump_out` decreases by `charge_step` volts. The output must not go below V(vss).
4. Between pulses, the output holds its value. Output transitions must use `transition()`.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| vth | 0.45 | Logic threshold for pulse detection |
| charge_step | 0.02 | Voltage increment/decrement per pulse |
| tedge | 50p | Output transition time |

## Constraints

- Must be pure voltage-domain
- Use `@(cross(...))` for edge detection
- Use `transition()` for output
- Do NOT use current-domain constructs (`I() <+`, `ddt()`, `idt()`)

## Public Evaluation Contract

```spectre
simulator lang=spectre
global 0
Vvdd (vdd 0) vsource dc=0.9 type=dc
Vvss (vss 0) vsource dc=0.0 type=dc
Vlead (lead_pulse 0) vsource type=pwl wave=[0 0  10e-9 0  10.1e-9 0.9  20e-9 0.9  20.1e-9 0  ... 90e-9 0  90.1e-9 0.9  100e-9 0.9  100.1e-9 0  300e-9 0]
Vlag (lag_pulse 0) vsource type=pwl wave=[0 0  150e-9 0  150.1e-9 0.9  160e-9 0.9  160.1e-9 0  ... 190e-9 0  190.1e-9 0.9  200e-9 0.9  200.1e-9 0  300e-9 0]
tran tran stop=300n maxstep=1n
save lead_pulse lag_pulse pump_out
```

The testbench sends 5 lead pulses (t=10-100ns) followed by 3 lag pulses (t=150-200ns). Expected: pump_out rises by ~5*charge_step, then falls by ~3*charge_step.

## Deliverables
Write your module to `dut.va`.
