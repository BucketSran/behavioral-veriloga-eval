Write a Verilog-A module named `cmp_hysteresis`.

# Task: comparator_hysteresis_smoke

## Objective

Create a differential comparator with hysteresis behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `cmp_hysteresis`
- **Ports** (all `electrical`, exactly as named): `vinn`, `vinp`, `out_n`, `out_p`, `vss`, `vdd`
- **Parameters**:
  - `vhys` (real, default `10e-3`)
  - `tedge` (real, default `50p`)
- **Behavior**:
  - Rising threshold: when `vinp - vinn` rises above `+vhys/2`, drive `out_p` HIGH and `out_n` LOW.
  - Falling threshold: when `vinp - vinn` falls below `-vhys/2`, drive `out_p` LOW and `out_n` HIGH.
  - Between thresholds, hold the previous decision.
  - Use TWO separate `@(cross(...))` statements for rising and falling thresholds.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `cmp_hysteresis.va` via `ahdl_include`
- Provides VDD=1.8V, VSS=0V
- Generates differential input as a slow ramp from -50mV to +50mV and back
- Uses vhys=10m parameter on instance
- Saves signals: `vinn`, `vinp`, `out_n`, `out_p`
- Runs transient for ~50us (slow ramp to show hysteresis window)

## Deliverable

Two files:
1. `cmp_hysteresis.va` - the Verilog-A behavioral model
2. `tb_cmp_hysteresis.scs` - the Spectre testbench

Expected behavior:
- Output should toggle when differential input crosses threshold with hysteresis
- Hysteresis window vhys should prevent chatter on slow ramps
Ports:
- `VINN`: input electrical
- `VINP`: input electrical
- `OUTN`: output electrical
- `OUTP`: output electrical
- `VSS`: inout electrical
- `VDD`: inout electrical
