# Flash Data Align Pipeline Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `flash_data_align_pipeline.va`:
  - Module `flash_data_align_pipeline` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `din0` (input, electrical)
    - position 2: `din1` (input, electrical)
    - position 3: `din2` (input, electrical)
    - position 4: `din3` (input, electrical)
    - position 5: `din4` (input, electrical)
    - position 6: `din5` (input, electrical)
    - position 7: `din6` (input, electrical)
    - position 8: `din7` (input, electrical)
    - position 9: `dout0` (output, electrical)
    - position 10: `dout1` (output, electrical)
    - position 11: `dout2` (output, electrical)
    - position 12: `dout3` (output, electrical)

## Public Parameter Contract

- `flash_data_align_pipeline.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_THERMOMETER_COUNT`: restore: At each rising `clk` crossing through `vth`, count all asserted thermometer inputs `din0` through `din7`. Required traces: `time`, `clk`, `din0`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `din7`.
- `P_FOUR_STAGE_ALIGNMENT`: restore: The sampled count is shifted through a four-stage alignment pipeline before it is published. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_BINARY_OUTPUT_ORDER`: restore: The delayed count is driven as voltage-coded binary with `dout0` as LSB and `dout3` as MSB. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_EVENT_HELD_OUTPUTS`: restore: Outputs update only from pipeline clock events and hold their previous voltage-coded state between events. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `flash_data_align_pipeline.va`.
Every supplied `.va` file is editable; do not add or omit files.
