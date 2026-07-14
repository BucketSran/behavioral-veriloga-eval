# Clocked ADC Quantizer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clocked ADC Quantizer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `flash_adc_3b.va`:
  - Module `flash_adc_3b` (entry)
    - position 0: `VDD` (input, electrical)
    - position 1: `VSS` (input, electrical)
    - position 2: `VIN` (input, electrical)
    - position 3: `CLK` (input, electrical)
    - position 4: `DOUT2` (output, electrical)
    - position 5: `DOUT1` (output, electrical)
    - position 6: `DOUT0` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `flash_adc_3b` as `XDUT` with ordered public binding: VDD=vdd, VSS=vss, VIN=vin, CLK=clk, DOUT2=dout2, DOUT1=dout1, DOUT0=dout0.

## Public Parameter Contract

- `flash_adc_3b.vrefp` defaults to `0.9` V; valid range: vrefp > vrefn; sets upper conversion endpoint.
- `flash_adc_3b.vrefn` defaults to `0.0` V; valid range: vrefn < vrefp; sets lower conversion endpoint.
- `flash_adc_3b.vth` defaults to `0.45` V; valid range: finite real; sets rising clock decision threshold.
- `flash_adc_3b.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets output-bit transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RISING_EDGE_QUANTIZATION`: exercise and make observable: At each rising CLK crossing, VIN is quantized into one of eight uniform bins spanning vrefn to vrefp. Required traces: `time`, `clk`, `vin`, `dout2`, `dout1`, `dout0`.
- `P_CODE_CLAMP`: exercise and make observable: Samples at or outside the conversion endpoints produce codes clamped to the inclusive range 0 through 7. Required traces: `time`, `clk`, `vin`, `dout2`, `dout1`, `dout0`.
- `P_BINARY_RAIL_ENCODING`: exercise and make observable: DOUT2 through DOUT0 encode the held code from MSB to LSB using VDD for one and VSS for zero. Required traces: `time`, `vdd`, `vss`, `dout2`, `dout1`, `dout0`.
- `P_CODE_MONOTONICITY`: exercise and make observable: For increasing VIN samples across the conversion range, the sampled three-bit code is nondecreasing. Required traces: `time`, `clk`, `vin`, `dout2`, `dout1`, `dout0`.
- `P_SAMPLE_HOLD`: exercise and make observable: The output code remains stable between rising CLK crossings even when VIN changes. Required traces: `time`, `clk`, `vin`, `dout2`, `dout1`, `dout0`.

The required trace names are: `time`, `vdd`, `vss`, `vin`, `clk`, `dout2`, `dout1`, `dout0`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
