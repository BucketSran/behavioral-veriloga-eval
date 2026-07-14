# Comparator Reset Low 1p8

## Task Contract

Implement `comparator_reset_low_1p8.va` as a clocked differential comparator DUT with reset-low decision outputs in a 1.8 V logic domain.

## Public Verilog-A Interface

Use this exact module signature:

```verilog
module comparator_reset_low_1p8(cmpck, vinn, vinp, dcmpn, dcmpp);
```

All ports are electrical. `cmpck` is the comparator clock, `vinp` and `vinn` are differential analog inputs, and `dcmpp`/`dcmpn` are voltage-coded decision outputs.

## Public Parameter Contract

Provide these overrideable public parameters:

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vdd` | `1.8` | Logic high level and clock threshold reference. |
| `td_cmp` | `100p` | Output decision delay. |

## Required Behavior

Initialize both decision outputs low. Whenever `cmpck` falls through `vdd/2`, reset both outputs low. Whenever `cmpck` rises through `vdd/2`, latch a differential decision: drive `dcmpp` high for `vinp > vinn`, drive `dcmpn` high for `vinp < vinn`, and keep both outputs low for an equal-input decision. Hold the latched or reset state until the next clock event.

## Modeling Constraints

Use event-driven voltage-domain Verilog-A and smoothed output voltage contributions. Do not add current contributions, transistor devices, checker logic, out-of-band test hooks, simulator side channels, or hard-coded testbench sample times. Update local decision state in analog event blocks and drive output contributions outside those event blocks.

## Output Contract

Return exactly one source artifact named `comparator_reset_low_1p8.va`.
