# Therm8 To Bin4 Count

## Task Contract

Implement `therm8_to_bin4_count.va` as an 8-input thermometer-popcount encoder with a 4-bit voltage-coded binary output.

## Public Verilog-A Interface

Use this module signature:

```verilog
module therm8_to_bin4_count(th0, th1, th2, th3, th4, th5, th6, th7, b0, b1, b2, b3);
```

All ports are scalar `electrical` nodes. `th0..th7` are thermometer-style voltage-coded inputs. `b0..b3` are the binary count outputs, with `b0` as the least significant bit.

## Public Parameter Contract

- `vth`: input decision threshold, default `0.45`.

## Required Behavior

- Count how many of `th0..th7` are above `vth`.
- Encode the count as a 4-bit binary word.
- Drive `b0..b3` as voltage-coded outputs with `b0` as the least significant bit.
- Support any input pattern by counting high inputs rather than assuming a perfectly monotonic thermometer prefix.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A only. Do not add checker logic, out-of-band test hooks, simulator side channels, current contributions, `ddt()`, or `idt()`.

## Output Contract

Return exactly one source artifact named `therm8_to_bin4_count.va`.
