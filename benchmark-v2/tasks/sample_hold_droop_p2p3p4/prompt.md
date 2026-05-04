# Task: capture_and_decay

Design a Verilog-A module named `capture_and_decay` that on a rising command edge captures the instantaneous voltage of an analog input and then lets the held output decay exponentially toward zero until the next capture event.

## Module Interface

| Port | Direction | Description |
|------|-----------|-------------|
| vdd | inout | Positive supply |
| vss | inout | Ground |
| sample_cmd | input | Capture command signal |
| analog_in | input | Analog voltage to be captured |
| held_value | output | Held value with exponential decay |

## Behavioral Specification

1. On each rising transition of `sample_cmd` (voltage crossing the logic threshold upward), the instantaneous voltage on `analog_in` is captured.
2. The captured voltage is clamped to the supply range [V(vss), V(vdd)].
3. Immediately after capture, `held_value` is driven to the captured level.
4. Between capture events, `held_value` decays exponentially toward zero with a user-specified time constant. The decay follows the continuous-time exponential law: held_value(t+dt) = held_value(t) * exp(-dt/tau).
5. Output transitions must use the `transition()` filter.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| vth | 0.45 | Logic threshold for sample_cmd |
| trf | 40p | Output transition rise/fall time |
| tau | 120n | Exponential decay time constant |
| dt | 0.5n | Decay evaluation time step |

## Constraints

- Must be pure voltage-domain (no `I() <+`, `ddt()`, `idt()`)
- Use `@(cross(...))` for edge detection
- Use `transition()` for output driving

## Negative Constraints

- This is NOT an ideal sample-and-hold ¡ª there must be visible exponential decay between captures
- This is NOT a continuous voltage follower ¡ª the output must remain frozen (with decay) between command edges
- Do NOT use a linear droop rate ¡ª the decay must be exponential (proportional to current value)

## Public Evaluation Contract

```spectre
simulator lang=spectre
global 0
Vvdd (vdd 0) vsource dc=0.9 type=dc
Vvss (vss 0) vsource dc=0.0 type=dc
Vsample (sample_cmd 0) vsource type=pulse val0=0 val1=0.9 delay=1n rise=50p fall=50p width=9n period=20n
Vanalog (analog_in 0) vsource type=pwl wave=[0 0.15 25e-9 0.15  25e-9 0.80 65e-9 0.80  65e-9 0.35 105e-9 0.35  105e-9 0.75 165e-9 0.75]
tran tran stop=170n maxstep=0.1n
save analog_in sample_cmd held_value
```

## Deliverables
Write your module to `dut.va`.
