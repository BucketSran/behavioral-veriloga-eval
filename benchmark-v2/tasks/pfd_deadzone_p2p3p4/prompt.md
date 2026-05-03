# Task: edge_arrival_detector

Design a Verilog-A module named `edge_arrival_detector` that senses which of two event-carrying inputs has a rising transition first, and asserts a corresponding output flag. When both flags become active simultaneously, a reset path must immediately clear both.

## Module Interface

| Port | Direction | Description |
|------|-----------|-------------|
| VDD | inout | Positive supply |
| VSS | inout | Ground |
| first_edge | input | First event input |
| second_edge | input | Second event input |
| lead_flag | output | Asserts high when first_edge arrives before second_edge |
| dn | output | Asserts high when second_edge arrives before first_edge |

## Behavioral Specification

1. On a rising transition of `first_edge` (voltage crosses the logic threshold upward), `lead_flag` is asserted high.
2. On a rising transition of `second_edge`, `dn` is asserted high.
3. When BOTH `lead_flag` and `dn` are high simultaneously, a reset mechanism must immediately clear both outputs back to low. This reset must be combinational (not clocked).
4. The outputs must never be high at the same time for more than the minimum reset path delay.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| vth | 0.45 | Logic threshold voltage |
| tedge | 20p | Output transition time |

## Constraints

- All outputs must use `transition()` filter
- Edge detection must use `@(cross(...))`
- Do NOT use current-domain constructs

## Negative Constraints

- This is NOT an XOR-based phase detector ¡ª do NOT drive the output as XOR of inputs
- This is NOT a Bang-Bang phase detector ¡ª do NOT use clocked flip-flops or state machines
- The reset mechanism must be purely combinational, NOT clock-synchronized

## Public Evaluation Contract

```spectre
simulator lang=spectre
global 0
Vvdd (vdd 0) vsource dc=0.9 type=dc
Vvss (vss 0) vsource dc=0.0 type=dc
Vfirst (first_edge 0) vsource type=pulse val0=0 val1=0.9 period=20n width=10n rise=20p fall=20p
Vsecond (second_edge 0) vsource type=pulse val0=0 val1=0.9 period=20n width=10n rise=20p fall=20p delay=100p
tran tran stop=300n maxstep=5p
save first_edge second_edge lead_flag dn
```

## Deliverables
Write your module to `dut.va`.
