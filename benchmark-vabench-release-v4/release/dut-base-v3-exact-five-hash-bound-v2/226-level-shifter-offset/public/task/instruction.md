# Level Shifter Offset

## Task Contract

Implement `level_shifter_offset.va` as a continuous analog level shifter.

## Public Verilog-A Interface

Use this module signature:

```verilog
module level_shifter_offset(sigin, sigout);
```

Both ports are scalar `electrical` nodes. `sigin` is the input voltage and `sigout` is the shifted output voltage.

## Public Parameter Contract

- `sigshift`: output offset added to the input, default `0.35`.

## Required Behavior

Drive `sigout` to `V(sigin) + sigshift` for the current input voltage.

## Modeling Constraints

Use direct continuous voltage-domain arithmetic. Do not invert the offset, add gain, clip the output, add undeclared state, emit checker logic, or depend on private stimulus timing.

## Output Contract

Return exactly one source artifact named `level_shifter_offset.va`.
