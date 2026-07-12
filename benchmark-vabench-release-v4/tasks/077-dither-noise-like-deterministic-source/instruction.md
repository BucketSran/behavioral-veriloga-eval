# Dither Noise Like Deterministic Source

## Task Contract

Implement the requested Verilog-A artifact for `Dither Noise Like Deterministic Source`.
- Form: `dut`
- Level: `L1`
- Category: `stimulus_source_generators`
- Target artifact(s): `noise_gen_ref.va`

Implement `noise_gen_ref.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `noise_gen` with positional ports `vin_i, vout_o`. Both ports
are electrical.

## Public Parameter Contract

- `sigma = 0.01 V`: perturbation amplitude/statistical scale before any
  example harness override.
- `dt = 0.5 ns`: sample interval before any example harness override.

## Required Behavior

Generate a sampled, zero-mean, noise-like deterministic perturbation and add it
to `V(vin_i)`. The output is piecewise constant between sample events:

```text
vout_o = V(vin_i) + sigma * sample
```

The normalized perturbation `sample` must repeat this public eight-sample sequence, advancing by one entry at each `dt` update:

```text
[-1.0, -0.5, 0.0, 0.5, 1.0, 0.5, 0.0, -0.5]
```

Every complete eight-sample period is exactly zero mean, and every perturbation must remain bounded within `[-sigma, +sigma]`.

Use a periodic timer-driven sample-and-hold style, such as `@(timer(0, dt))`,
so the perturbation is updated once per sample interval rather than recomputed
at every analog evaluation point or sampled only once. The task models a
bounded dither/noise-like stimulus source for transient behavioral benches; it
does not require physical noise analysis.

## Modeling Constraints

Return only `noise_gen_ref.va`. Do not generate a the simulator example harness or validation harness
logic. Do not use random simulator distributions, current contributions, `ddt()`, `idt()`, transistor-level
devices, AC/noise analysis, or simulator-specific side channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `noise_gen_ref.va`. Do not include explanatory prose outside the source artifact contents.
