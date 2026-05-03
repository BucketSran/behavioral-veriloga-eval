# Task: window_comparator

Design a Verilog-A module named `window_comparator` that compares an analog input voltage against two reference thresholds and produces three digital outputs indicating which voltage region the input falls into.

## Module Interface

| Port | Direction | Description |
|------|-----------|-------------|
| vdd | inout | Positive supply |
| vss | inout | Ground |
| signal_in | input | Analog voltage to be compared |
| above_hi | output | High when signal_in > vref_hi |
| in_window | output | High when vref_lo <= signal_in <= vref_hi |
| below_lo | output | High when signal_in < vref_lo |

## Behavioral Specification

The module continuously monitors `signal_in` and compares it against two fixed thresholds:

- `above_hi` outputs V(vdd) when V(signal_in) > vref_hi, otherwise V(vss).
- `in_window` outputs V(vdd) when vref_lo <= V(signal_in) <= vref_hi, otherwise V(vss).
- `below_lo` outputs V(vdd) when V(signal_in) < vref_lo, otherwise V(vss).

At any given time, exactly one of the three outputs should be high (the regions are mutually exclusive and cover the full voltage range). All outputs must use `transition()` for edge shaping.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| vref_hi | 0.7 | Upper threshold voltage |
| vref_lo | 0.2 | Lower threshold voltage |
| tedge | 50p | Output transition time |

## Constraints

- Must be pure voltage-domain (no `I() <+`, `ddt()`, `idt()`)
- Use `transition()` for all outputs
- Do NOT add hysteresis unless explicitly specified

## Public Evaluation Contract

```spectre
simulator lang=spectre
global 0
Vvdd (vdd 0) vsource dc=0.9 type=dc
Vvss (vss 0) vsource dc=0.0 type=dc
Vvin (signal_in 0) vsource type=pwl wave=[0 0.0  100e-9 0.0  101e-9 0.15  200e-9 0.15  201e-9 0.45  300e-9 0.45  301e-9 0.75  400e-9 0.75  401e-9 0.9  500e-9 0.9]
tran tran stop=500n maxstep=1n
save signal_in above_hi in_window below_lo
```

The testbench ramps `signal_in` through 5 regions in sequence: below_lo (0V), below_lo (0.15V), in_window (0.45V), above_hi (0.75V), above_hi (0.9V).
Expected: each phase has exactly one output high, with clean transitions at the threshold crossings.

## Deliverables
Write your module to `dut.va`.
