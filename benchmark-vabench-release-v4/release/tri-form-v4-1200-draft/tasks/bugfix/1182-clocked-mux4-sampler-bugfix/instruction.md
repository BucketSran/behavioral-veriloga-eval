# Clocked Mux4 Sampler Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clocked_mux4_sampler.va`:
  - Module `clocked_mux4_sampler` (entry)
    - position 0: `dsel0` (input, electrical)
    - position 1: `dsel1` (input, electrical)
    - position 2: `din0` (input, electrical)
    - position 3: `din1` (input, electrical)
    - position 4: `din2` (input, electrical)
    - position 5: `din3` (input, electrical)
    - position 6: `update` (input, electrical)
    - position 7: `rst` (input, electrical)
    - position 8: `clks` (input, electrical)
    - position 9: `dout` (output, electrical)

## Public Parameter Contract

- `clocked_mux4_sampler.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `clocked_mux4_sampler.tdel` defaults to `1p`; valid range: finite; overrides tdel.
- `clocked_mux4_sampler.tr` defaults to `20p`; valid range: finite; overrides tr.
- `clocked_mux4_sampler.tf` defaults to `20p`; valid range: finite; overrides tf.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_SELECTS_DIN0`: restore: While `rst` is high, the selected channel and `dout` are forced to `din0`. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`, `rst`, `update`.
- `P_FALLING_CLOCK_UPDATE_SAMPLE`: restore: On each falling `clks` crossing with reset inactive and `update` high, latch `dsel0/dsel1` and sample the selected input. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`, `rst`, `update`.
- `P_UPDATE_LOW_HOLDS_STATE`: restore: On falling `clks` crossings with `update` low, hold the previous selection and output value. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`, `rst`, `update`.
- `P_SELECT_DECODE_AND_OUTPUT_TIMING`: restore: The held two-bit selection maps to `din0..din3` in binary order and drives `dout` with the declared transition timing. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`, `rst`, `update`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clocked_mux4_sampler.va`.
Every supplied `.va` file is editable; do not add or omit files.
