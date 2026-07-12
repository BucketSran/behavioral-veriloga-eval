# Enable Gated Clock Pulse

## Task Contract

Implement the requested Verilog-A artifact for `Enable Gated Clock Pulse`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `enable_gated_clock_pulse.va`

Implement `enable_gated_clock_pulse.va`, a voltage-coded enable-qualified clock/control pulse gate for AMS sampled-data timing.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate a the simulator example harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
Declare module `enable_gated_clock_pulse` with the positional ports listed below.
```

Inputs are `clk` and `en`. Output is `pulse`. All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Treat `clk` and `en` as voltage-coded logic using `vth`.
- Drive `pulse` high exactly when both `clk` and `en` are high.
- Drive `pulse` low otherwise.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `enable_gated_clock_pulse.va`.
