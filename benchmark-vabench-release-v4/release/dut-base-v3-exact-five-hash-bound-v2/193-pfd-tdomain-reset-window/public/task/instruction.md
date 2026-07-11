# PFD Time-Domain Reset Window

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: PLL/phase-frequency detector primitive.
- Target artifact: `pfd_tdomain_reset_window.va`.
- Role: rail-referenced PFD with timed reset overlap window.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module pfd_tdomain_reset_window(in1, in2, up, dn, vdd, gnd);
```

`in1` and `in2` are phase input edges, `up` and `dn` are PFD outputs, and `vdd/gnd` define output rails and thresholds. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `ttol = 5f`, `td = 0`, `tt = 10p`, and `ton = 120p`. Derive logic threshold from the `vdd` and `gnd` pins.

## Required Behavior

A leading `in1` edge asserts `up`; a leading `in2` edge asserts `dn`. When both inputs have arrived, keep both outputs asserted for the reset-overlap window `ton`, then clear both states. Use the public delay and transition parameters for output shaping and hold states between events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `pfd_tdomain_reset_window.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
