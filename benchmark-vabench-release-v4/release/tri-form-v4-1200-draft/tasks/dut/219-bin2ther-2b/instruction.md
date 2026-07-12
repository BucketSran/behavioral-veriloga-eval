# Bin2ther 2b

## Task Contract

Implement `bin2ther_2b.va` as a small voltage-domain binary-to-segment decoder used as a data-converter support component.

## Public Verilog-A Interface

Use this module signature:

```verilog
module bin2ther_2b(vdd, gnd, b1, b0, t0, t1, t2);
```

All ports are scalar `electrical` nodes. `vdd` and `gnd` define the local output rails, `b1`/`b0` are voltage-coded input bits, and `t0..t2` are voltage-coded segment outputs.

## Public Parameter Contract

This task has no public scalar parameters. The switching threshold is the midpoint of the local `vdd` and `gnd` rails.

## Required Behavior

- Interpret `b1` and `b0` relative to the local rail midpoint.
- Drive `t0` and `t1` high together when `b1` is high.
- Drive `t2` high when `b0` is high.
- Drive each low output to the local `gnd` rail and each high output to the local `vdd` rail.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A only. Do not add checker logic, out-of-band test hooks, simulator side channels, current contributions, `ddt()`, or `idt()`.

## Output Contract

Return exactly one source artifact named `bin2ther_2b.va`.
