# Smooth Absolute Value

## Task Contract
Implement `absolute_value.va`, a memoryless smooth absolute-value / soft-rectifier analog primitive DUT.

## Public Verilog-A Interface
Declare module `absolute_value(sigin, sigout)` with scalar electrical ports. `sigin` is the input voltage and `sigout` is the output voltage.

## Public Parameter Contract
Provide one overrideable public parameter:

- `smooth = 0.05 V from (0:inf)`: smoothing voltage that rounds the cusp around zero.

## Required Behavior
Drive `sigout` as the smooth absolute-value transfer `V(sigin) * tanh(V(sigin) / smooth)`. The transfer should be even in the input, nonnegative, deterministic, memoryless, and rounded near zero instead of using a sharp ideal absolute-value cusp. For large positive and negative inputs, the output should approach the corresponding input magnitude.

## Modeling Constraints
Use voltage contributions only. Do not emit or modify support testbenches, checker logic, out-of-band test hooks, hard-code testbench waveform sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Output Contract
Return exactly one source artifact named `absolute_value.va`.
