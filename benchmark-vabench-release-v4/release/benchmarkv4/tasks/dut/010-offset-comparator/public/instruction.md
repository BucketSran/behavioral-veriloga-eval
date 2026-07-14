# Offset Comparator

## Task Contract

Implement one Verilog-A DUT artifact for a clocked voltage-domain comparator with a positive input-referred offset.

- Target artifact: `cmp_offset_ref.va`

## Public Verilog-A Interface

Declare module `cmp_offset_ref` with positional ports `VDD, VSS, CLK, VINP, VINN, OUT_P`. All ports are electrical. `VDD` and `VSS` are supply rails, `CLK` is the sampling clock, `VINP` and `VINN` are the differential analog inputs, and `OUT_P` is the voltage-coded latched decision output.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vos = 5 mV`: positive input-referred offset threshold.
- `tt = 20 ps`: transition smoothing time for `OUT_P`.

## Required Behavior

- Initialize `OUT_P` low relative to `VSS`.
- On each rising crossing of `CLK` through the local rail midpoint, latch whether `V(VINP,VSS) - V(VINN,VSS)` is greater than `vos`.
- Drive `OUT_P` high to the `VDD` rail only for latched inputs above the positive offset threshold; otherwise drive it low to `VSS`.
- Hold the latched decision between rising clock edges, even if the input polarity changes between samples.
- Use smoothed rail-referenced voltage-domain output transitions.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A. Use voltage contributions only; do not use current contributions, `ddt()`, or `idt()`. For clocked behavior, update local state in analog event blocks and place the output voltage contribution outside those event blocks. Do not add extra ports, files, debug outputs, pass/fail flags, or state observables that are not part of the public interface.

## Output Contract

Return exactly one complete source artifact named `cmp_offset_ref.va`.
