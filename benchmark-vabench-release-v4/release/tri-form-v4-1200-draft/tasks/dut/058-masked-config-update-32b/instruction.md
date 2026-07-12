# Masked Config Update 32b

## Task Contract

Implement the requested Verilog-A artifact for `Masked Config Update 32b`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `masked_config_update_32b.va`

Implement `masked_config_update_32b.va`, a voltage-coded masked trim/configuration-update helper for AMS calibration and mode-control flows.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate a the simulator example harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
module masked_config_update_32b(old_cfg, new_cfg, mask, out_cfg);
    input [31:0] old_cfg, new_cfg, mask;
    output [31:0] out_cfg;
```

All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Treat `old_cfg`, `new_cfg`, and `mask` as voltage-coded logic using `vth`.
- For each bit `N`, drive `out_cfg[N]` from `new_cfg[N]` when `mask[N]` is high.
- Otherwise drive `out_cfg[N]` from `old_cfg[N]`.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Compact loop-based Verilog-A is preferred for the 32-bit buses.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `masked_config_update_32b.va`.
