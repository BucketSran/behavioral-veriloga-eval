# Smooth Limiting Diffamp

## Task Contract
Implement `limiting_diffamp.va`, a centered differential gain stage with smooth tanh output limiting.

## Public Verilog-A Interface
Declare module `limiting_diffamp(sigin_p, sigin_n, sigout)` with scalar electrical ports. `sigin_p` and `sigin_n` form the differential input; `sigout` is the output voltage.

## Public Parameter Contract
Provide overrideable public parameters:

- `gain = 4.0`: small-signal differential gain near zero differential input.
- `limit = 0.75 V from (0:inf)`: symmetric soft output limiting magnitude.

## Required Behavior
Compute the differential input from `sigin_p` to `sigin_n`, preserve polarity, and drive a smooth odd transfer that is approximately `gain * V(sigin_p, sigin_n)` near zero while asymptotically approaching `+limit` and `-limit` for large positive and negative differential inputs. The limiting behavior should be continuous and smooth rather than a hard clamp.

## Modeling Constraints
Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Output Contract
Return exactly one source artifact named `limiting_diffamp.va`.
