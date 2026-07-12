# DAC Serial Accumulator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dac_serial_accumulator.va`:
  - Module `dac_serial_accumulator` (entry)
    - position 0: `clk_sample` (input, electrical)
    - position 1: `clk_sarready` (input, electrical)
    - position 2: `data` (input, electrical)
    - position 3: `out` (output, electrical)

## Public Parameter Contract

- `dac_serial_accumulator.vdd` defaults to `1.1`; valid range: finite; overrides vdd.
- `dac_serial_accumulator.vcm` defaults to `0.55`; valid range: finite; overrides vcm.
- `dac_serial_accumulator.bit_count` defaults to `4`; valid range: finite; overrides bit_count.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SAMPLE_CLOCK_RESET`: restore: Each falling `clk_sample` crossing resets the accumulator and serial bit counter. Required traces: `time`, `clk_sample`, `out`.
- `P_SARREADY_SERIAL_ACCUMULATION`: restore: Falling `clk_sarready` crossings during the active bit window add the sampled `data` bit to the accumulator. Required traces: `time`, `clk_sarready`, `data`, `out`.
- `P_BINARY_WEIGHT_ORDER`: restore: The first accepted serial bit has the largest binary weight and later bits use descending weights. Required traces: `time`, `clk_sarready`, `data`, `out`.
- `P_BIPOLAR_OUTPUT_MAPPING`: restore: The accumulated code is mapped to the required bipolar output range rather than an unipolar code. Required traces: `time`, `out`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dac_serial_accumulator.va`.
Every supplied `.va` file is editable; do not add or omit files.
