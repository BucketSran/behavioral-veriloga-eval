# Ideal ADC 4bit Quantizer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ideal_adc_4bit_quantizer.va`:
  - Module `ideal_adc_4bit_quantizer` (entry)
    - position 0: `vclk` (input, electrical)
    - position 1: `vip` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `digital` (output, electrical)

## Public Parameter Contract

- `ideal_adc_4bit_quantizer.trise` defaults to `20p from [0:inf)`; valid range: finite; overrides trise.
- `ideal_adc_4bit_quantizer.tfall` defaults to `20p from [0:inf)`; valid range: finite; overrides tfall.
- `ideal_adc_4bit_quantizer.tdel` defaults to `0 from [0:inf)`; valid range: finite; overrides tdel.
- `ideal_adc_4bit_quantizer.vtrans_clk` defaults to `0.5 from (0:inf)`; valid range: finite; overrides vtrans_clk.
- `ideal_adc_4bit_quantizer.vref` defaults to `1.0 from (0:inf)`; valid range: finite; overrides vref.
- `ideal_adc_4bit_quantizer.levels` defaults to `16 from (0:inf)`; valid range: finite; overrides levels.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_DIFFERENTIAL_SAMPLE`: restore: Each rising `vclk` crossing through `vtrans_clk` samples `V(vip)-V(vin)` and holds the resulting analog code on `digital` until the next sample. Required traces: `time`, `digital`, `vclk`, `vin`, `vip`.
- `P_SYMMETRIC_INPUT_RANGE`: restore: The sampled differential input is quantized over the symmetric span from `-vref` to `+vref`; values outside that span saturate to the endpoint codes. Required traces: `time`, `digital`, `vclk`, `vin`, `vip`.
- `P_CODE_SCALE_AND_LSB`: restore: `digital` represents the selected code using the declared `levels` spacing so adjacent quantization bins differ by one LSB. Required traces: `time`, `digital`, `vclk`, `vin`, `vip`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ideal_adc_4bit_quantizer.va`.
Every supplied `.va` file is editable; do not add or omit files.
