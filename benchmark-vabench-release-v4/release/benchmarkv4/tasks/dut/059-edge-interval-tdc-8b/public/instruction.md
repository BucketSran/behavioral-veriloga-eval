# Edge Interval TDC 8b

## Task Contract

Implement the requested Verilog-A artifact for `Edge Interval TDC 8b`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `edge_interval_tdc_8b.va`

Implement `edge_interval_tdc_8b.va`, a example harness utility that measures the elapsed time between voltage-coded start and stop edges and reports the result as an 8-bit code.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate the validation harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
Declare module `edge_interval_tdc_8b` with the positional ports listed below.
```

Inputs are `start` and `stop`. Outputs are `valid` and `code0` through `code7`. All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- On each rising `start` crossing, arm a new measurement, store the start time, and clear `valid`.
- On the next rising `stop` crossing after an armed start, compute `round((stop_time - start_time) / 1 ns)`.
- Saturate the code to the inclusive range 0 to 255.
- Drive `code0` as the least significant bit through `code7` as the most significant bit, and assert `valid` after a completed measurement.
- Ignore unarmed `stop` edges.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Use event state for the armed flag, start time, result code, and validity flag.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `edge_interval_tdc_8b.va`.
