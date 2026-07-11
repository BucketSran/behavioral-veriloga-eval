# Duty Cycle Meter 8b

## Task Contract

Implement the requested Verilog-A artifact for `Duty Cycle Meter 8b`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `duty_cycle_meter_8b.va`

Implement `duty_cycle_meter_8b.va`, a voltage-domain instrumentation helper that measures clock high-time fraction over complete cycles and reports the duty cycle as an 8-bit code.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate a the simulator example harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
Declare module `duty_cycle_meter_8b` with the positional ports listed below.
```

Input is `clk_in`. Outputs are `valid` and `duty0` through `duty7`. All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Record each rising and falling threshold crossing of `clk_in`.
- For each complete cycle with one falling edge between two rising edges, compute `round(255 * high_time / period)`.
- Saturate the code to 0 through 255.
- Drive `duty0` as the least significant bit through `duty7` as the most significant bit.
- Assert and hold `valid` after a duty-cycle measurement has been made.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Use event state for rise time, fall time, measured code, and validity flag.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `duty_cycle_meter_8b.va`.
