# Config Shift Register 64b

## Task Contract

Implement the requested Verilog-A artifact for `Config Shift Register 64b`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `config_shift_reg_64b.va`

Implement `config_shift_reg_64b.va`, a clocked serial-to-parallel trim/configuration loader for voltage-coded AMS calibration and mode-control models.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate the validation harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
module config_shift_reg_64b(clk, rst_n, serial_in, q);
    input clk, rst_n, serial_in;
    output [63:0] q;
```

All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Treat `clk`, `rst_n`, and `serial_in` as voltage-coded logic using `vth`.
- On each rising `clk` crossing, clear all register bits if `rst_n` is low.
- Otherwise shift `serial_in` into `q[0]`, previous `q[0]` into `q[1]`, and so on through `q[63]`.
- Drive `q[63:0]` as the current parallel register state.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Keep register state in integer or real state variables updated by clock events; avoid combinational rewrites that ignore history.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `config_shift_reg_64b.va`.
