# Slew Rate Limiter

## Task Contract

Implement one Verilog-A DUT artifact for a discrete-time slew-rate limiter.

- Target artifact: `slew_rate_limiter.va`

## Public Verilog-A Interface

Declare module `slew_rate_limiter(vin, vout)` with scalar electrical voltage-domain ports.

## Public Parameter Contract

Provide these overrideable public parameters:

- `step = 0.015 V`: maximum internal output change per update.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- Initialize the internal output state to `0 V`.
- Update the state only on a periodic `1 ns` timer.
- On each update, move the internal state toward `V(vin)` by no more than `step`.
- Limit both rising and falling changes.
- If `V(vin)` is within one `step` of the internal state, the state may settle directly to `V(vin)`.
- Drive `vout` from the internal state with a smoothed voltage contribution.
- The response must eventually reach both high and low input levels while remaining slower than an instantaneous copy of `vin`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A. Use voltage contributions only; do not use current contributions, `ddt()`, or `idt()`. Do not add extra ports, files, debug outputs, pass/fail flags, or state observables that are not part of the public interface.

## Output Contract

Return exactly one complete source artifact named `slew_rate_limiter.va`.
