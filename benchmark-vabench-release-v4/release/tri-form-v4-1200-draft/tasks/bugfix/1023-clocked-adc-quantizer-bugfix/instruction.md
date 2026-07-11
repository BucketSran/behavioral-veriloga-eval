# Clocked ADC Quantizer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `flash_adc_3b.va`:
  - Module `flash_adc_3b` (entry)
    - position 0: `VDD` (input, electrical)
    - position 1: `VSS` (input, electrical)
    - position 2: `VIN` (input, electrical)
    - position 3: `CLK` (input, electrical)
    - position 4: `DOUT2` (output, electrical)
    - position 5: `DOUT1` (output, electrical)
    - position 6: `DOUT0` (output, electrical)

## Public Parameter Contract

- `flash_adc_3b.vrefp` defaults to `0.9` V; valid range: vrefp > vrefn; sets upper conversion endpoint.
- `flash_adc_3b.vrefn` defaults to `0.0` V; valid range: vrefn < vrefp; sets lower conversion endpoint.
- `flash_adc_3b.vth` defaults to `0.45` V; valid range: finite real; sets rising clock decision threshold.
- `flash_adc_3b.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets output-bit transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_EDGE_QUANTIZATION`: restore: At each rising CLK crossing, VIN is quantized into one of eight uniform bins spanning vrefn to vrefp. Required traces: `time`, `clk`, `vin`, `dout2`, `dout1`, `dout0`.
- `P_CODE_CLAMP`: restore: Samples at or outside the conversion endpoints produce codes clamped to the inclusive range 0 through 7. Required traces: `time`, `clk`, `vin`, `dout2`, `dout1`, `dout0`.
- `P_BINARY_RAIL_ENCODING`: restore: DOUT2 through DOUT0 encode the held code from MSB to LSB using VDD for one and VSS for zero. Required traces: `time`, `vdd`, `vss`, `dout2`, `dout1`, `dout0`.
- `P_CODE_MONOTONICITY`: restore: For increasing VIN samples across the conversion range, the sampled three-bit code is nondecreasing. Required traces: `time`, `clk`, `vin`, `dout2`, `dout1`, `dout0`.
- `P_SAMPLE_HOLD`: restore: The output code remains stable between rising CLK crossings even when VIN changes. Required traces: `time`, `clk`, `vin`, `dout2`, `dout1`, `dout0`.

## Modeling Constraints

- Use rising-edge event-driven quantization and held state.
- Use smoothed voltage contributions only.
- Do not use current contributions, transistor-level devices, ddt(), idt(), or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `flash_adc_3b.va`.
Every supplied `.va` file is editable; do not add or omit files.
