# Deterministic Jittered Clock Source

## Task Contract

Implement the requested Verilog-A artifact for `Deterministic Jittered Clock Source`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `deterministic_jittered_clock.va`

Implement `deterministic_jittered_clock.va`, a repeatable voltage-domain jittered clock stimulus source for timing-margin and aperture-stress checks, whose cycle-to-cycle timing can be deterministically modulated by an 8-bit seed.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate a the simulator example harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
Declare module `deterministic_jittered_clock` with the positional ports listed below.
```

Inputs are `jitter_en` and seed bits `seed0` through `seed7`. Output is `clk_out`. All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Generate `clk_out` as a 0-to-`vdd` deterministic clock.
- With `jitter_en` low, use a constant 20 ns period, i.e. a 10 ns nominal half-period.
- With `jitter_en` high, sample `seed7:seed0` through `vth` at each output transition, interpret it as an unsigned seed, and apply repeatable edge-to-edge half-period modulation.
- A seed input change affects the next half-period computed after the next output transition; it must not move an already scheduled current edge.
- For edge index `k`, update the next half-period as `10 ns + (((seed + 3*k) % 5) - 2) * 0.8 ns`.
- With a constant seed and `jitter_en` state, the resulting modulo-5 half-period sequence repeats every five output transitions.
- Keep every resulting full clock period bounded and repeatable for the same seed.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Use timer-driven state for the output level, edge index, seed capture, and next-edge time.
- Do not use random distribution functions; the jitter is deterministic and seed-dependent.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `deterministic_jittered_clock.va`.
