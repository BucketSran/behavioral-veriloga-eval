# Task: External-Mechanism Hysteresis Comparator (Offset Variant)

Implement an EVAS-compatible voltage-domain hysteresis comparator (Schmitt-like behavior).

## Required output file

- `dut.va`

## Module contract

Create module `hysteresis_cmp_window_offset` with ports:

- `sense_in` (input, electrical)
- `decision_out` (output, electrical)

## Behavior

1. Parameters:
   - `vhigh = 1.2`
   - `vlow = 0.0`
   - `vth_rise = 0.65`
   - `vth_fall = 0.35`
   - `trise = 500p`
   - `tfall = 500p`
2. Hysteresis rule:
   - when `sense_in` rises across `vth_rise`, output goes high
   - when `sense_in` falls across `vth_fall`, output goes low
3. Output is held otherwise (stateful behavior).

## Negative constraints

1. Do not use a single-threshold stateless comparator.
2. Do not use current-domain contributions.
3. Do not use `ddt()` or `idt()`.
