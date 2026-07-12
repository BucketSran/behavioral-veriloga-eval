# Comparator Offset Driver Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `comparator_offset_binary_driver.va`:
  - Module `comparator_offset_binary_driver` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `dcmpp` (input, electrical)
    - position 2: `vinp` (output, electrical)
    - position 3: `vinn` (output, electrical)

## Public Parameter Contract

- `comparator_offset_binary_driver.vdd` defaults to `0.9`; valid range: finite; overrides vdd.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FALLING_CLOCK_DECISION_SAMPLE`: restore: On each falling `clk` threshold crossing, sample `dcmpp` to choose the next binary-search direction. Required traces: `time`, `clk`, `dcmpp`, `vinp`, `vinn`.
- `P_DECISION_POLARITY_UPDATE`: restore: A high decision moves the differential input negative and a low decision moves it positive. Required traces: `time`, `clk`, `dcmpp`, `vinp`, `vinn`.
- `P_HALVING_SEARCH_STEP`: restore: The differential search step halves after each sampled decision. Required traces: `time`, `clk`, `dcmpp`, `vinp`, `vinn`.
- `P_COMMON_MODE_HALF_SCALE_DRIVE`: restore: `vinp` and `vinn` are driven symmetrically around the common-mode level with half differential amplitude on each side. Required traces: `time`, `vinp`, `vinn`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `comparator_offset_binary_driver.va`.
Every supplied `.va` file is editable; do not add or omit files.
