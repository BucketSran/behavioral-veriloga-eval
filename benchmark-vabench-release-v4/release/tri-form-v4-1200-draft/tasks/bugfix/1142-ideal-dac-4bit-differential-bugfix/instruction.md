# Ideal DAC 4bit Differential Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ideal_dac_4bit_differential.va`:
  - Module `ideal_dac_4bit_differential` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `digital` (input, electrical)
    - position 2: `vcm` (input, electrical)
    - position 3: `vop` (output, electrical)
    - position 4: `von` (output, electrical)

## Public Parameter Contract

- `ideal_dac_4bit_differential.trise` defaults to `20p from [0:inf)`; valid range: finite; overrides trise.
- `ideal_dac_4bit_differential.tfall` defaults to `20p from [0:inf)`; valid range: finite; overrides tfall.
- `ideal_dac_4bit_differential.tdel` defaults to `0 from [0:inf)`; valid range: finite; overrides tdel.
- `ideal_dac_4bit_differential.vref` defaults to `1.0 from (0:inf)`; valid range: finite; overrides vref.
- `ideal_dac_4bit_differential.vtrans_clk` defaults to `0.5 from (0:inf)`; valid range: finite; overrides vtrans_clk.
- `ideal_dac_4bit_differential.levels` defaults to `16 from (0:inf)`; valid range: finite; overrides levels.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FALLING_EDGE_CODE_SAMPLE`: restore: Each falling `clk` crossing through `vtrans_clk` samples `digital`, clamps it to the valid code range, and holds the converted output until the next sample. Required traces: `time`, `clk`, `digital`, `vcm`, `von`, `vop`.
- `P_MIDRISE_DIFFERENTIAL_SCALE`: restore: The sampled code maps to a mid-rise differential DAC level with the declared `levels` and `vref` scale. Required traces: `time`, `clk`, `digital`, `vcm`, `von`, `vop`.
- `P_OUTPUT_POLARITY_AND_COMMON_MODE`: restore: `vop` and `von` are complementary about `vcm`, with positive differential polarity for larger sampled codes. Required traces: `time`, `clk`, `digital`, `vcm`, `von`, `vop`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ideal_dac_4bit_differential.va`.
Every supplied `.va` file is editable; do not add or omit files.
