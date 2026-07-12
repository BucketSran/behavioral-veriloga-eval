# L2 7b DAC Ready Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `l2_7b_dac_ready.va`:
  - Module `l2_7b_dac_ready` (entry)
    - position 0: `din1` (input, electrical)
    - position 1: `din2` (input, electrical)
    - position 2: `din3` (input, electrical)
    - position 3: `din4` (input, electrical)
    - position 4: `din5` (input, electrical)
    - position 5: `din6` (input, electrical)
    - position 6: `din7` (input, electrical)
    - position 7: `rdy` (input, electrical)
    - position 8: `aout` (output, electrical)

## Public Parameter Contract

- `l2_7b_dac_ready.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `l2_7b_dac_ready.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FIRST_READY_EDGE_ARMS_ONLY`: restore: The first rising `rdy` edge arms the DAC and leaves the initialized output at zero. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `din7`, `rdy`.
- `P_READY_SAMPLES_SEVEN_BITS`: restore: Each later rising `rdy` edge samples `din1..din7` against `vth` with the declared switched-capacitor weights. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `din7`, `rdy`.
- `P_BIPOLAR_WEIGHTED_DAC_OUTPUT`: restore: Map the sampled 7-bit weight to the declared bipolar single-ended output with the correct denominator and offset. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `din7`, `rdy`.
- `P_DAC_OUTPUT_LEVEL_AND_HOLD`: restore: Hold `aout` between ready edges and drive the declared voltage scale without half-level errors. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `din5`, `din6`, `din7`, `rdy`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `l2_7b_dac_ready.va`.
Every supplied `.va` file is editable; do not add or omit files.
