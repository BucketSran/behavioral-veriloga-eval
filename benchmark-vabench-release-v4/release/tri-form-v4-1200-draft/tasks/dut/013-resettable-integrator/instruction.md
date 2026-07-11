# Resettable Integrator

## Task Contract

Implement one Verilog-A DUT artifact for a timer-updated resettable integrator.

- Target artifact: `resettable_integrator.va`

## Public Verilog-A Interface

Declare module `resettable_integrator(vin, rst, vout)` with scalar electrical voltage-domain ports. `rst` is a voltage-coded active-high control input.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: reset logic threshold.
- `gain = 1.0e9 1/s`: integration gain.
- `dt = 1 ns`: timer update interval.
- `vmax = 0.85 V`: accumulator upper clamp level.
- `tr = 500 ps`: output transition smoothing time.

## Required Behavior

- Initialize the internal accumulator to `0 V`.
- Update state only on `@(timer(0, dt))`.
- Treat reset as active high when `V(rst) > vth`; while reset is active, force the accumulator and `vout` toward `0 V`.
- When reset is low, add `gain * V(vin) * dt` to the accumulator on each timer event.
- Clamp the accumulator to the closed range from `0 V` to `vmax`.
- After reset deasserts, integration must restart from `0 V` using the same update rule.
- Drive `vout` from the accumulator with a smoothed voltage contribution.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A. Use voltage contributions only; do not use current contributions, `ddt()`, or `idt()`. Do not add extra ports, files, debug outputs, pass/fail flags, or state observables that are not part of the public interface.

## Output Contract

Return exactly one complete source artifact named `resettable_integrator.va`.
