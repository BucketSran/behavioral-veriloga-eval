# Clock Sample 1600n Sequencer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clock_sample_1600n_sequencer.va`:
  - Module `clock_sample_1600n_sequencer` (entry)
    - position 0: `rst` (output, electrical)
    - position 1: `s` (output, electrical)
    - position 2: `nc` (output, electrical)
    - position 3: `res` (output, electrical)
    - position 4: `conv` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PERIODIC_16NS_FRAME`: restore: Generate a repeating 16 ns ADC timing frame. Required traces: `time`, `conv`, `nc`, `res`, `rst`, `s`.
- `P_RESET_AND_SAMPLE_WINDOWS`: restore: `rst` and `s` are high only in the declared frame windows, including both sample windows. Required traces: `time`, `conv`, `nc`, `res`, `rst`, `s`.
- `P_NONOVERLAP_AND_RESIDUE_WINDOWS`: restore: `nc` and `res` use the declared non-overlap and residue windows without swapping outputs. Required traces: `time`, `conv`, `nc`, `res`, `rst`, `s`.
- `P_CONVERSION_OUTPUT_TIMING`: restore: `conv` is asserted in the declared conversion windows with valid timing and level. Required traces: `time`, `conv`, `nc`, `res`, `rst`, `s`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clock_sample_1600n_sequencer.va`.
Every supplied `.va` file is editable; do not add or omit files.
