# Thermometer To Binary Encoder 8b

## Task Contract

Implement the requested Verilog-A artifact for `Thermometer To Binary Encoder 8b`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `therm_to_bin_8b.va`

Implement `therm_to_bin_8b.va`, the inverse utility of the 8-bit thermometer decoder. It converts a cumulative 256-line voltage-coded thermometer input into an 8-bit binary count plus a validity flag.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate the validation harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
module therm_to_bin_8b(th, b, valid);
    input [255:0] th;
    output [7:0] b;
    output valid;
```

All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Treat every `th[N]` input as voltage-coded logic using `vth`.
- A valid thermometer word is cumulative from `th[0]`: exactly `th[0]` through `th[count-1]` are high and all higher inputs are low.
- Code 0 is valid and means all thermometer inputs are low.
- Code 255 is valid and means `th[0]` through `th[254]` are high and `th[255]` is low.
- For a valid word, drive `b[7:0]` to the unsigned count with `b[7]` as the most significant bit and drive `valid` high.
- For a non-cumulative or otherwise invalid word, drive `valid` low and drive `b[7:0]` to zero.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Compact loop-based Verilog-A is preferred; do not manually expand 256 input checks unless required by the simulator subset.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `therm_to_bin_8b.va`.
