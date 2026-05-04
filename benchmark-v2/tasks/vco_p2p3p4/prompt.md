# Task: voltage_controlled_oscillator

Design a Verilog-A module named `voltage_controlled_oscillator` that generates a square wave whose frequency is a linear function of an analog control voltage.

## Module Interface

| Port | Direction | Description |
|------|-----------|-------------|
| vdd | inout | Positive supply |
| vss | inout | Ground |
| tune_voltage | input | Analog control voltage |
| periodic_out | output | Square wave output |

## Behavioral Specification

The module produces a periodic binary output that toggles between vdd and vss. The output frequency must be a linear function of the control voltage:

- When `tune_voltage` is at or below `vmin` (0V), the output oscillates at `fmin` (10 MHz).
- When `tune_voltage` is at or above `vmax` (0.9V), the output oscillates at `fmax` (100 MHz).
- Between vmin and vmax, frequency varies linearly: f = fmin + (fmax - fmin) * (V(tune_voltage) - vmin) / (vmax - vmin).

The output must have approximately 50% duty cycle and use `transition()` for edge shaping. The oscillation must be self-sustaining (no external clock required).

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| vmin | 0.0 | Control voltage lower bound |
| vmax | 0.9 | Control voltage upper bound |
| fmin | 10e6 | Minimum output frequency (Hz) at vmin |
| fmax | 100e6 | Maximum output frequency (Hz) at vmax |
| vth | 0.45 | Logic threshold |
| tedge | 50p | Output transition time |

## Constraints

- Must be pure voltage-domain (no `I() <+`)
- Use `@(timer(...))` for oscillation timing
- Use `transition()` for output
- Do NOT use `$abstime` to drive the output directly

## Public Evaluation Contract

```spectre
simulator lang=spectre
global 0
Vvdd (vdd 0) vsource dc=0.9 type=dc
Vvss (vss 0) vsource dc=0.0 type=dc
Vtune (tune_voltage 0) vsource type=pwl wave=[0 0.0  2000e-9 0.0  2001e-9 0.225  4000e-9 0.225  4001e-9 0.45  6000e-9 0.45  6001e-9 0.675  8000e-9 0.675  8001e-9 0.9  10000e-9 0.9]
tran tran stop=10000n maxstep=1n
save tune_voltage periodic_out
```

## Deliverables
Write your module to `dut.va`.
