# Task: flash_adc_3b_smoke

## Objective

Write a Verilog-A behavioral module for a **3-bit Flash ADC**.

## Specification

- **Module name**: `flash_adc_3b`
- **Ports**: `VDD` (inout), `VSS` (inout), `VIN` (input), `CLK` (input), `DOUT2`..`DOUT0` (output) — all `electrical`
- **Parameters**: `vrefp` (real, default 0.9), `vrefn` (real, default 0.0), `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - Full-scale range: `vrefn` to `vrefp`, divided into 8 equal bins (LSB = (vrefp−vrefn)/8).
  - On rising `CLK` edge, compute `code = floor((V(VIN) − vrefn) / LSB)`, clamp to [0, 7].
  - Drive `DOUT2..DOUT0` with the binary code.
- **Output**: use `transition()`. No `idt`, `ddt`, or `I() <+`.

## Constraints

- Pure voltage-domain.
- Implement encoding directly with `floor()` — do NOT enumerate 7 individual comparator chains.
- Use `$strobe` to log each conversion.

## Deliverable

A single `.va` file: `flash_adc_3b.va`.
