# First Order Lowpass

## Task Contract

Implement one Verilog-A DUT artifact for a discrete-time first-order low-pass filter.

- Target artifact: `first_order_lowpass.va`

## Public Verilog-A Interface

Declare module `first_order_lowpass(vin, vout)` with scalar electrical voltage-domain ports.

## Public Parameter Contract

Provide these overrideable public parameters:

- `alpha = 0.025`: low-pass update coefficient.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- Initialize the internal output state to `0 V`.
- Update the state only on a periodic `500 ps` timer.
- At each update, apply `y = y + alpha * (V(vin) - y)`.
- Drive `vout` from the internal state with a smoothed voltage contribution.
- For a positive input step, the response must be monotone, bounded by the input level, and slower than an instantaneous copy of `vin`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A. Use voltage contributions only; do not use current contributions, `ddt()`, or `idt()`. Do not add extra ports, files, debug outputs, pass/fail flags, or state observables that are not part of the public interface.

## Output Contract

Return exactly one complete source artifact named `first_order_lowpass.va`.
