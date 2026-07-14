# ADC Sample Clock Sequencer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `adc_sample_clock_sequencer.va`:
  - Module `adc_sample_clock_sequencer` (entry)
    - position 0: `rst` (output, electrical)
    - position 1: `s` (output, electrical)
    - position 2: `ss` (output, electrical)
    - position 3: `nc_az` (output, electrical)
    - position 4: `nc` (output, electrical)
    - position 5: `conv` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PERIODIC_18NS_FRAME`: restore: Generate a repeating 18 ns timing frame. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.
- `P_RESET_SAMPLE_AND_SS_WINDOWS`: restore: `rst`, `s`, and `ss` are high only in the declared frame windows. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.
- `P_NONOVERLAP_AND_AUTOZERO_WINDOWS`: restore: `nc` and `nc_az` use the declared non-overlap and autozero windows without swapping outputs. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.
- `P_CONVERSION_WINDOW_TIMING`: restore: `conv` is asserted in the declared conversion windows with the correct phase. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.
- `P_TIMING_OUTPUT_LEVELS`: restore: All timing outputs drive valid voltage-coded low/high levels. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `adc_sample_clock_sequencer.va`.
Every supplied `.va` file is editable; do not add or omit files.
