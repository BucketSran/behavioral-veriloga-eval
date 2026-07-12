# Flash ADC Threshold Taps Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `flash_adc_threshold_taps.va`:
  - Module `flash_adc_threshold_taps` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `dout0` (output, electrical)
    - position 3: `dout1` (output, electrical)
    - position 4: `dout2` (output, electrical)
    - position 5: `dout3` (output, electrical)
    - position 6: `dout4` (output, electrical)
    - position 7: `dout5` (output, electrical)
    - position 8: `dout6` (output, electrical)

## Public Parameter Contract

- `flash_adc_threshold_taps.vrefp` defaults to `0.125`; valid range: finite; overrides vrefp.
- `flash_adc_threshold_taps.vrefn` defaults to `-0.125`; valid range: finite; overrides vrefn.
- `flash_adc_threshold_taps.vl` defaults to `0.0`; valid range: finite; overrides vl.
- `flash_adc_threshold_taps.vh` defaults to `0.9`; valid range: finite; overrides vh.
- `flash_adc_threshold_taps.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_SELECTED_THRESHOLD_TAPS`: restore: Each rising `clk` crossing compares `vin` against the selected threshold taps and updates all thermometer outputs. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`, `dout5`, `dout6`, `vin`.
- `P_THERMOMETER_POLARITY`: restore: Outputs assert high when `vin` exceeds their associated threshold and low otherwise. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`, `dout5`, `dout6`, `vin`.
- `P_OUTPUT_HIGH_LEVEL`: restore: Asserted thermometer outputs use `vh` and inactive outputs use `vl`. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`, `dout5`, `dout6`, `vin`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `flash_adc_threshold_taps.va`.
Every supplied `.va` file is editable; do not add or omit files.
