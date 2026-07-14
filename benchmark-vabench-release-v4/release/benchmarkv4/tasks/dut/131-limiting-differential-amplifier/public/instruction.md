# Limiting Differential Amplifier

## Task Contract
Implement the Verilog-A DUT `limiting_differential_amplifier.va` for a differential-input single-ended amplifier with output limiting.

## Public Verilog-A Interface
Provide `module limiting_differential_amplifier(sigin_p, sigin_n, sigout);` with electrical inputs `sigin_p`, `sigin_n` and electrical output `sigout`.

## Public Parameter Contract
Expose real parameters `gain = 1`, `sigout_high = 10`, `sigout_low = -10`, and `sigin_offset = 0`. Testbenches may override these parameters.

## Required Behavior
Read `V(sigin_p, sigin_n)`, subtract the input-referred offset, multiply by `gain`, and center the result at the midpoint of `sigout_high` and `sigout_low`. Clamp the final output target to the inclusive output rail interval.

## Modeling Constraints
Use real-valued analog arithmetic and one voltage contribution to `sigout`. Do not omit the offset, remove the clamp, use current contributions, or add filtering that changes the static transfer.

## Output Contract
Submit only the completed Verilog-A module in `limiting_differential_amplifier.va`.
