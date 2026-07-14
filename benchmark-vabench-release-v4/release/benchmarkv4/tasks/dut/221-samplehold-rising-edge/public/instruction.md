# Samplehold Rising Edge

## Task Contract

Implement `samplehold_rising_edge.va` as a rising-edge sampled voltage-domain sample-and-hold.

## Public Verilog-A Interface

Use this module signature:

```verilog
module samplehold_rising_edge(control, vin, vout);
```

All ports are scalar `electrical` nodes. `control` is the voltage-coded sampling control, `vin` is the analog input voltage, and `vout` is the held output voltage.

## Public Parameter Contract

- `thresh`: rising-edge control threshold, default `2.5`.
- `tdel`: output transition delay, default `20p`.
- `tr`: output rise/fall smoothing time, default `20p`.

## Required Behavior

- Sample `vin` on each rising `control` crossing of `thresh`.
- Hold the sampled voltage on `vout` until the next rising control crossing.
- Do not continuously track `vin` between sample events.
- Drive `vout` with smooth voltage-domain output behavior.

## Modeling Constraints

Use voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, simulator side channels, current contributions, `ddt()`, or `idt()`.

## Output Contract

Return exactly one source artifact named `samplehold_rising_edge.va`.
