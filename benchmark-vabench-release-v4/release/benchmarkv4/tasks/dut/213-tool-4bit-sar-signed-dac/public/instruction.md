# Tool 4bit SAR Signed DAC

## Task Contract

Implement `tool_4bit_sar_signed_dac.va` as a sample-triggered signed SAR reconstruction DAC DUT. Although it is a helper-style circuit macro, the public row evaluates this module as a standalone data-converter component.

## Public Verilog-A Interface

Use this exact module signature:

```verilog
module tool_4bit_sar_signed_dac(d0, d1, d2, d3, sh, aout);
```

All ports are electrical. `d0..d3` are voltage-coded decision bits, `sh` is the sample trigger, and `aout` is the signed analog output.

## Public Parameter Contract

Provide these overrideable public parameters:

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vth` | `0.9` | Logic threshold for `sh` and `d0..d3`. |
| `gain` | `1.8 / 16.0` | Output scale applied to the signed weighted sum. |
| `tr` | `1p` | Output transition time. |

## Required Behavior

On each rising crossing of `sh` through `vth`, evaluate bits `d3..d0` with weights `8, 4, 2, 1`. A high bit contributes the positive weight and a low bit contributes the negative weight. Drive `aout` to the signed weighted sum multiplied by `gain` and hold it until the next sample trigger.

## Modeling Constraints

Use event-driven voltage-domain Verilog-A. Do not hard-code visible stimulus timing, testbench sample points, checker-only expected values, current contributions, transistor devices, or simulator side channels.

## Output Contract

Return exactly one source artifact named `tool_4bit_sar_signed_dac.va`.
