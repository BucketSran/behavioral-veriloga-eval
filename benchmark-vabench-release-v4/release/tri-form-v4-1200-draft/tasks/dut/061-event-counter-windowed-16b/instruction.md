# Event Counter Windowed 16b

## Task Contract

Implement the requested Verilog-A artifact for `Event Counter Windowed 16b`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `event_counter_windowed_16b.va`

Implement `event_counter_windowed_16b.va`, a voltage-domain timing/readout instrumentation block that counts event edges inside an enable window and reports the final count.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate a the simulator example harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
Declare module `event_counter_windowed_16b` with the positional ports listed below.
```

Inputs are `gate` and `event_in`. Outputs are `done` and `count0` through `count15`. All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- On a rising `gate` crossing, clear the counter, mark the window active, and drive `done` low.
- Count rising `event_in` crossings only while the window is active and `gate` is high.
- On a falling `gate` crossing, close the window, hold the count, and assert `done`.
- Drive `count0` as the least significant bit through `count15` as the most significant bit.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Use event state for the active-window flag, count, and done flag.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `event_counter_windowed_16b.va`.
