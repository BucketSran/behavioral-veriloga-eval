# DAC Restore 4bit Clocked Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dac_restore_4bit_clocked.va`:
  - Module `dac_restore_4bit_clocked` (entry)
    - position 0: `d3` (input, electrical)
    - position 1: `d2` (input, electrical)
    - position 2: `d1` (input, electrical)
    - position 3: `d0` (input, electrical)
    - position 4: `clk` (input, electrical)
    - position 5: `vout` (output, electrical)

## Public Parameter Contract

- `dac_restore_4bit_clocked.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_EACH_RISING_CLK_CROSSING_DECODE`: restore: On each rising `clk` crossing, decode `d3..d0` as a 4-bit binary word and drive `vout` to the center of that code bin across a bipolar 1.8 V span from `-0.9 V` to `+0.9 V`. Hold the output between clock events. Required traces: `time`, `clk`, `d0`, `d1`, `d2`, `d3`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dac_restore_4bit_clocked.va`.
Every supplied `.va` file is editable; do not add or omit files.
