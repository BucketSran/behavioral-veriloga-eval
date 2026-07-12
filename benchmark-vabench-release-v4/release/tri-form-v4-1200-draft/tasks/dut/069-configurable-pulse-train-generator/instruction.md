# Configurable Pulse Train Generator

## Task Contract

Implement the requested Verilog-A artifact for `Configurable Pulse Train Generator`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `configurable_pulse_train.va`

Implement `configurable_pulse_train.va`, a clocked finite pulse-train sequencer for AMS calibration, startup, and sampled-data control timing.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate a the simulator example harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
Declare module `configurable_pulse_train` with the positional ports listed below.
```

Inputs are `clk`, `start`, 4-bit `period`, 4-bit `width`, and 4-bit `count`. Outputs are `pulse` and `done`. All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Sample controls on rising `clk` crossings.
- While idle, a sampled high `start` captures unsigned 4-bit `period`, `width`, and `count` control words.
- Interpret each captured control word as at least one clock sample: zero-coded period, width, or count values map to 1.
- Emit exactly `count` pulses. Each pulse is high for `width` clock samples, and pulse starts are separated by `period` clock samples.
- After the final pulse completes, drive `pulse` low and assert `done`.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Use clocked state for running/idle state, captured controls, tick count, emitted-pulse count, pulse output, and done flag.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `configurable_pulse_train.va`.
