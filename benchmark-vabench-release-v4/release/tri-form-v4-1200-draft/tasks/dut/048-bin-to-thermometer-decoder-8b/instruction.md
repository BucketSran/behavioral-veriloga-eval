# Bin To Thermometer Decoder 8b

## Task Contract

Implement the requested Verilog-A artifact for `Binary To Thermometer Decoder 8b`.
- Form: `dut`
- Level: `L1`
- Category: `example harness_utility_modules`
- Target artifact(s): `bin_to_therm_8b.va`

Implement `bin_to_therm_8b.va`, a voltage-domain unary-DAC element-selection decoder used by data-converter support models to expand an 8-bit binary word into a cumulative thermometer bus.

- This is a DUT/support-component task: implement only the requested Verilog-A source artifact.
- Do not generate a the simulator example harness or validation harness.
- Preserve the public module name, port order, port directions, and parameter names.
- Treat any public validation harness as an observable use case, not as values to hard-code into the DUT.

## Public Verilog-A Interface

```verilog
module bin_to_therm_8b(en, b, th);
    input en;
    input [7:0] b;
    output [255:0] th;
```

All ports are electrical.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `0.9` | Logic-high output voltage. |
| `vth` | `0.45` | Decision threshold for voltage-coded digital inputs. |
| `tr` | `20p` | Output transition rise/fall smoothing time. |

## Required Behavior

- Treat `en` and `b[7:0]` as voltage-coded logic inputs using `vth`.
- Decode `b[7:0]` as an unsigned integer from 0 to 255, with `b[7]` as the most significant bit.
- When `en` is high, drive exactly `code` thermometer outputs high as a prefix from `th[0]` upward: `th[0]` through `th[code-1]` high and all higher bits low.
- Code 0 drives every thermometer output low. Code 255 drives `th[0]` through `th[254]` high and `th[255]` low.
- When `en` is low, drive every thermometer output low.

## Modeling Constraints

- Keep the model pure voltage-domain behavioral Verilog-A.
- Treat voltage-coded logic low as near 0 V and logic high as near `vdd`.
- Use `transition(...)` or equivalent smooth voltage contributions for driven logic outputs.
- Do not instantiate transistor-level devices, use current-branch contributions, AC/noise analysis, validation logic, validation-only hooks, or simulator-specific side channels.
- Compact loop-based Verilog-A is preferred; do not manually expand 256 scalar output assignments unless required by the simulator subset.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A source file named `bin_to_therm_8b.va`.
