# Decision Router Logic

## Task Contract

Implement `decision_router_logic.va` as a voltage-coded decision router that exposes route flags and decision monitor outputs.

## Public Verilog-A Interface

Use this module signature:

```verilog
module decision_router_logic(vin1, vin2, valid, x, y, z, dm, dl);
```

All ports are scalar `electrical` nodes. `vin1`, `vin2`, and `valid` are voltage-coded logic inputs. `x`, `y`, `z`, `dm`, and `dl` are voltage-coded outputs.

## Public Parameter Contract

- `vth`: input decision threshold, default `0.45`.
- `vh`: output high level, default `0.9`.

## Required Behavior

- Interpret `vin1`, `vin2`, and `valid` relative to `vth`.
- Drive `dm` high when `vin1` is high.
- Drive `dl` high when `vin1` is low and `vin2` is high.
- Drive `x` high when `valid` is high and both decision inputs are low.
- Drive `y` high when `valid` is high and both decision inputs are high.
- Drive `z` high when `valid` is high, `vin1` is low, and `vin2` is high.
- Drive all other listed outputs low under their inactive conditions.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A only. Do not add checker logic, out-of-band test hooks, simulator side channels, current contributions, `ddt()`, or `idt()`.

## Output Contract

Return exactly one source artifact named `decision_router_logic.va`.
