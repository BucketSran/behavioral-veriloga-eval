# Linear PFD Gain

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: PLL/phase-detector analog primitive.
- Target artifact: `linear_pfd_gain.va`.
- Role: deterministic linear PFD gain macro.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module linear_pfd_gain(in1, in2, out);
```

All ports are scalar `electrical` ports. `in1` and `in2` are analog inputs; `out` is the analog gain output.

## Public Parameter Contract

Provide overrideable parameter `kphi = 2.03`. It is the deterministic phase-detector gain coefficient. Stochastic noise terms are out of scope for this benchmark.

## Required Behavior

Drive `out` continuously as the gain coefficient times the input difference `in1 - in2`. The output should track analog input changes without clocked state or clipping.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `linear_pfd_gain.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
