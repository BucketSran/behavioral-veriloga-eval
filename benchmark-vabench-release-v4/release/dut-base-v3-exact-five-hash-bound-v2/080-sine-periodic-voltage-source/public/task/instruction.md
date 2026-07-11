# Sine Periodic Voltage Source

## Task Contract

Implement the requested Verilog-A artifact for `Sine Periodic Voltage Source`.
- Form: `dut`
- Level: `L1`
- Category: `stimulus_source_generators`
- Target artifact(s): `multitone.va`

Implement `multitone.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `multitone` with positional ports `VSS, OUT`. `VSS` is the
electrical reference input and `OUT` is the electrical output.

## Public Parameter Contract

Provide these overrideable real parameters:

- `f1 = 1.0e6 Hz`, `f2 = 2.0e6 Hz`, `f3 = 3.0e6 Hz`
- `a1 = 0.2 V`, `a2 = 0.1 V`, `a3 = 0.05 V`

## Required Behavior

Drive `OUT` with a three-tone voltage source:

```text
V(OUT,VSS) = a1*sin(2*pi*f1*t) + a2*sin(2*pi*f2*t) + a3*sin(2*pi*f3*t)
```

Use `$bound_step(...)` or equivalent timestep guidance based on the highest
tone frequency so the waveform is well resolved in transient simulation.

## Modeling Constraints

Return only `multitone.va`. Do not generate a the simulator example harness or validation harness
logic. Do not use current contributions, `ddt()`, transistor-level devices,
AC/noise analysis, or simulator-specific side channels.
Drive `OUT` relative to the declared `VSS` reference port.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `multitone.va`. Do not include explanatory prose outside the source artifact contents.
