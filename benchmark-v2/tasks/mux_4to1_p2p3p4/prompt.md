# Task: signal_router

Design a Verilog-A module named `signal_router` that routes one of four analog input lanes to a single output based on a 2-pin selection code.

## Module Interface

| Port | Direction | Description |
|------|-----------|-------------|
| VDD | inout | Positive supply |
| VSS | inout | Ground |
| lane_3 | input | Analog input lane 3 (selected when pick=3) |
| lane_2 | input | Analog input lane 2 (selected when pick=2) |
| lane_1 | input | Analog input lane 1 (selected when pick=1) |
| lane_0 | input | Analog input lane 0 (selected when pick=0) |
| pick_1 | input | Selection code MSB |
| pick_0 | input | Selection code LSB |
| routed | output | The selected lane voltage routed to output |

## Behavioral Specification

This module continuously examines the two digital selection pins that form a 2-bit code where pick_1 is the more significant bit. At any moment it drives the output to mirror the voltage of the input lane corresponding to the current selection code.

The output must update whenever any of the four lane inputs or either selection pin changes state (detected via threshold crossing). The output voltage must pass through a transition() filter.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| vth | 0.45 | Logic threshold voltage for selection pins |
| tedge | 100p | Output transition rise/fall time |

## Constraints

- Use standard `disciplines.vams` and `constants.vams` includes
- Use `@(cross(...))` for edge detection on all inputs
- Drive output through `transition()` filter
- Do NOT use current-domain constructs (`V() <+` only)

## Negative Constraints

- This module has a **single output** - it is NOT a demultiplexer (1-to-N)
- It is NOT a crossbar switch or router with multiple simultaneous outputs
- The output is a direct copy of the selected input voltage, not a sum or weighted combination

## Public Evaluation Contract

```spectre
simulator lang=spectre
global 0
Vvdd (vdd 0) vsource dc=0.9 type=dc
Vvss (vss 0) vsource dc=0.0 type=dc
Vlane3 (lane_3 0) vsource dc=0.8 type=dc
Vlane2 (lane_2 0) vsource dc=0.6 type=dc
Vlane1 (lane_1 0) vsource dc=0.3 type=dc
Vlane0 (lane_0 0) vsource dc=0.1 type=dc
Vpick1 (pick_1 0) vsource type=pwl wave=[0 0  200e-9 0  201e-9 0.9  400e-9 0.9]
Vpick0 (pick_0 0) vsource type=pwl wave=[0 0  100e-9 0  101e-9 0.9  200e-9 0.9  201e-9 0  300e-9 0  301e-9 0.9  400e-9 0.9]
tran tran stop=420n maxstep=1n
save lane_0 lane_1 lane_2 lane_3 pick_0 pick_1 routed
```

## Deliverables
Write your module to `dut.va`.
