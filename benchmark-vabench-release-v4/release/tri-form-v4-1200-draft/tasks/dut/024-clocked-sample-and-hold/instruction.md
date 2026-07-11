# Clocked Sample And Hold

## Task Contract

Implement one Verilog-A DUT artifact for a clocked sample-and-hold cell.

- Target artifact: `sample_hold.va`

## Public Verilog-A Interface

Declare module `sample_hold(VDD, VSS, IN, CLK, OUT)` with scalar electrical voltage-domain ports.

- `VDD`, `VSS`: local supply rails.
- `IN`: analog input voltage to be sampled.
- `CLK`: voltage-coded sampling clock.
- `OUT`: held analog output voltage.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: clock threshold.
- `tedge = 100 ps`: output transition smoothing time.

## Required Behavior

- Sample `IN` on each rising `CLK` crossing of `vth`.
- Hold the sampled voltage on `OUT` between rising clock crossings.
- Do not continuously track `IN` while the clock is between sample events.
- Drive `OUT` with smooth voltage-domain behavior referenced to the local rails.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A. Use voltage contributions only; do not use current contributions, `ddt()`, or `idt()`. Do not add extra ports, files, debug outputs, pass/fail flags, or state observables that are not part of the public interface.

## Output Contract

Return exactly one complete source artifact named `sample_hold.va`.
