# Task: parallel_to_serial_converter

Design a Verilog-A module named `parallel_to_serial_converter` that latches 8 parallel data pins on a latch command edge, then shifts them out one bit at a time on each subsequent shift clock edge, most significant bit first.

## Module Interface

| Port | Direction | Description |
|------|-----------|-------------|
| VDD | inout | Positive supply |
| VSS | inout | Ground |
| p7..p0 | input | 8-bit parallel data input (p7=MSB, p0=LSB) |
| latch_cmd | input | Latch command: rising edge captures parallel data |
| shift_clock | input | Shift clock: rising edge advances to next output bit |
| serial_stream | output | Serial output stream, MSB-first |

## Behavioral Specification

1. On a rising edge of `latch_cmd`, the module samples all 8 data pins and stores them internally.
2. On the first rising edge of `shift_clock` after latching (with `latch_cmd` low), the most significant bit (p7) appears on `serial_stream`.
3. On each subsequent rising edge of `shift_clock`, the next bit in MSB-to-LSB order is shifted out.
4. After all 8 bits have been shifted out, `serial_stream` holds at the last transmitted value until the next latch event.
5. All outputs use `transition()` filter.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| vth | 0.45 | Logic threshold voltage |
| tedge | 100p | Output transition time |

## Constraints

- Must be pure voltage-domain
- Use `@(cross(...))` for edge detection
- Drive outputs through `transition()`

## Negative Constraints

- Bits must be transmitted MSB-first (p7 first, p0 last), NOT LSB-first
- This is NOT a general-purpose shift register with configurable direction
- Do NOT implement a parallel-load shift register that accepts serial input

## Public Evaluation Contract

```spectre
simulator lang=spectre
global 0
Vvdd (vdd 0) vsource dc=0.9 type=dc
Vvss (vss 0) vsource dc=0.0 type=dc
Vp7 (p7 0) vsource dc=0.9 type=dc
Vp6 (p6 0) vsource dc=0.0 type=dc
Vp5 (p5 0) vsource dc=0.9 type=dc
Vp4 (p4 0) vsource dc=0.0 type=dc
Vp3 (p3 0) vsource dc=0.0 type=dc
Vp2 (p2 0) vsource dc=0.9 type=dc
Vp1 (p1 0) vsource dc=0.0 type=dc
Vp0 (p0 0) vsource dc=0.9 type=dc
Vlatch (latch_cmd 0) vsource type=pulse val0=0 val1=0.9 period=200n delay=5n width=12.5n rise=100p fall=100p
Vclk (shift_clock 0) vsource type=pulse val0=0 val1=0.9 period=5n delay=10n width=2.5n rise=100p fall=100p
tran tran stop=300n maxstep=1n
save latch_cmd shift_clock serial_stream
```

## Deliverables
Write your module to `dut.va`.
