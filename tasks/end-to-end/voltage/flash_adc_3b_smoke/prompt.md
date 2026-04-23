Write a Verilog-A module named `flash_adc_3b`.

# Task: flash_adc_3b_smoke

## Objective

Create a 3-bit Flash ADC behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `flash_adc_3b`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `vin`, `clk`, `dout2`, `dout1`, `dout0`
- **Parameters**: `vrefp` (real, default 0.9), `vrefn` (real, default 0.0), `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - Full-scale range: `vrefn` to `vrefp`, divided into 8 equal bins (LSB = (vrefp−vrefn)/8).
  - On rising `clk` edge, compute `code = floor((V(vin) − vrefn) / LSB)`, clamp to [0, 7].
  - Drive `dout2` (MSB), `dout1`, `dout0` (LSB) with the binary code.
-  No `idt`, `ddt`, or `I() <+`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `flash_adc_3b.va` via `ahdl_include`
- Provides VDD=0.9V, VSS=0V
- Generates a clock with period suitable for sampling
- Creates input voltage sweeping from 0 to 0.9V (full scale)
- Saves signals: `clk`, `vin`, `dout2`, `dout1`, `dout0`
- Runs transient long enough to see all 8 codes

## Deliverable

Two files:
1. `flash_adc_3b.va` - the Verilog-A behavioral model
2. `tb_flash_adc_3b.scs` - the Spectre testbench

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `VIN`: input electrical
- `CLK`: input electrical
- `DOUT2`: output electrical
- `DOUT1`: output electrical
- `DOUT0`: output electrical
