# Configurable Polarity Edge Detector

## Task Contract

Implement the requested Verilog-A artifact for `Configurable Polarity Edge Detector`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `configurable_polarity_edge_detector.va`

Implement `configurable_polarity_edge_detector.va`, a voltage-domain selectable-polarity edge qualification block for mixed-signal timing/readout flows.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate a the simulator example harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
Declare module `configurable_polarity_edge_detector` with the positional ports listed below.
```

Inputs are `sig` and `rise_en`. Output is `pulse`. All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Treat `sig` and `rise_en` as voltage-coded logic using `vth`.
- When `rise_en` is high, generate a short pulse after each rising edge of `sig` and do not pulse on falling edges.
- When `rise_en` is low, generate a short pulse after each falling edge of `sig` and do not pulse on rising edges.
- The output pulse width should be a short support-timing pulse, nominally about 2 ns, with smooth edges.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Use edge events and a clear timer or equivalent state so the pulse is bounded in time.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `configurable_polarity_edge_detector.va`.
