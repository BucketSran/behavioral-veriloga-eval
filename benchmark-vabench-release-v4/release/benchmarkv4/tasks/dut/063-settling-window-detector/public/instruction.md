# Settling Window Detector

## Task Contract

Implement the requested Verilog-A artifact for `Settling Window Detector`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `settling_window_detector.va`

Implement `settling_window_detector.va`, a voltage-domain instrumentation helper that detects when an analog signal has stayed inside a target tolerance window for a required hold time.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate the validation harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
Declare module `settling_window_detector` with the positional ports listed below.
```

Inputs are `vin`, `target`, and `tol`. Outputs are `settled` and `t_code0` through `t_code7`. All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Treat the input as in-window when `abs(V(vin) - V(target)) <= V(tol)`.
- When the signal first enters the window, record the entry time and drive `settled` low.
- If the signal leaves the window, clear the entry state, drive `settled` low, and clear the time code.
- Assert `settled` only after the signal has remained continuously in-window for at least 20 ns.
- Drive `t_code[7:0]` to `round(entry_time / 1 ns)`, saturated to the 8-bit range, with `t_code0` as the least significant bit.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded outputs as logic low near 0 V and logic high near `vdd`; this module has no voltage-coded digital inputs.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Keep continuous window qualification and the stored entry time consistent; do not report settled during the initial hold interval.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `settling_window_detector.va`.
