# Ready/Valid Latency Counter 12b

## Task Contract

Implement the requested Verilog-A artifact for `Ready/Valid Latency Counter 12b`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `ready_valid_latency_counter_12b.va`

Implement `ready_valid_latency_counter_12b.va`, a clocked converter/readout instrumentation block that measures the number of clock cycles from a sampled valid request to a sampled ready response.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate the validation harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
Declare module `ready_valid_latency_counter_12b` with the positional ports listed below.
```

Inputs are `clk`, `valid_i`, and `ready_i`. Outputs are `done` and `lat0` through `lat11`. All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Sample `valid_i` and `ready_i` on rising `clk` crossings.
- While idle, a sampled high `valid_i` starts a latency measurement with count zero and clears `done`.
- While active, increment the count on each rising clock where `ready_i` is sampled low.
- When `ready_i` is sampled high while active, latch the current count to `lat[11:0]`, assert `done`, and return to idle.
- If `valid_i` and `ready_i` are both sampled high on the starting edge, report zero latency.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Use clocked event state for active/idle state, cycle count, latched output code, and done flag.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `ready_valid_latency_counter_12b.va`.
