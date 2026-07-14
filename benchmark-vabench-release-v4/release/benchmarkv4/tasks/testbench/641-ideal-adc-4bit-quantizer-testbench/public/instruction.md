# Ideal ADC 4bit Quantizer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Ideal ADC 4bit Quantizer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ideal_adc_4bit_quantizer.va`:
  - Module `ideal_adc_4bit_quantizer` (entry)
    - position 0: `vclk` (input, electrical)
    - position 1: `vip` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `digital` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ideal_adc_4bit_quantizer` as `XDUT` with ordered public binding: vclk=vclk, vip=vip, vin=vin, digital=digital.

## Public Parameter Contract

- `ideal_adc_4bit_quantizer.trise` defaults to `20p from [0:inf)`; valid range: finite; overrides trise.
- `ideal_adc_4bit_quantizer.tfall` defaults to `20p from [0:inf)`; valid range: finite; overrides tfall.
- `ideal_adc_4bit_quantizer.tdel` defaults to `0 from [0:inf)`; valid range: finite; overrides tdel.
- `ideal_adc_4bit_quantizer.vtrans_clk` defaults to `0.5 from (0:inf)`; valid range: finite; overrides vtrans_clk.
- `ideal_adc_4bit_quantizer.vref` defaults to `1.0 from (0:inf)`; valid range: finite; overrides vref.
- `ideal_adc_4bit_quantizer.levels` defaults to `16 from (0:inf)`; valid range: finite; overrides levels.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_DIFFERENTIAL_SAMPLE`: exercise and make observable: Each rising `vclk` crossing through `vtrans_clk` samples `V(vip)-V(vin)` and holds the resulting analog code on `digital` until the next sample. Required traces: `time`, `digital`, `vclk`, `vin`, `vip`.
- `P_SYMMETRIC_INPUT_RANGE`: exercise and make observable: The sampled differential input is quantized over the symmetric span from `-vref` to `+vref`; values outside that span saturate to the endpoint codes. Required traces: `time`, `digital`, `vclk`, `vin`, `vip`.
- `P_CODE_SCALE_AND_LSB`: exercise and make observable: `digital` represents the selected code using the declared `levels` spacing so adjacent quantization bins differ by one LSB. Required traces: `time`, `digital`, `vclk`, `vin`, `vip`.

The required trace names are: `time`, `digital`, `vclk`, `vin`, `vip`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
