# ADC Zoom Timing Sequencer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `adc_zoom_timing_sequencer.va`:
  - Module `adc_zoom_timing_sequencer` (entry)
    - position 0: `rst` (output, electrical)
    - position 1: `s` (output, electrical)
    - position 2: `sar` (output, electrical)
    - position 3: `res` (output, electrical)
    - position 4: `intg` (output, electrical)
    - position 5: `clk_sar` (output, electrical)
    - position 6: `zoom` (output, electrical)
    - position 7: `clk_zoom` (output, electrical)
    - position 8: `rst_zoom` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_GENERATE_A_REPEATING_32_NS_COMPACT`: restore: Generate a repeating 32 ns compact ADC timing frame with these high windows: `rst` from 0.5 to 0.8 ns; `s` from 1.5 to 2.5 ns; `sar` from 3.0 to 5.4 ns; `clk_sar` from 3.0 to 3.25 ns, 3.6 to 3.85 ns, and 4.2 to 4.45 ns; `res` from 6.0 to 6.6 ns; `intg` from 8.0 to 8.7 ns; `zoom` from 9.2 to 10.8 ns; `clk_zoom` from 9.2 to 9.45 ns and 9.8 to 10.05 ns; and `rst_zoom` from 11.0 to 11.5 ns. All outputs should return low between their public windows and repeat every 32 ns. Required traces: `time`, `clk_sar`, `clk_zoom`, `intg`, `res`, `rst`, `rst_zoom`, `s`, `sar`, `zoom`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `adc_zoom_timing_sequencer.va`.
Every supplied `.va` file is editable; do not add or omit files.
