# VA Lx DAC Ideal 4b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `va_lx_dac_ideal_4b.va`:
  - Module `va_lx_dac_ideal_4b` (entry)
    - position 0: `din1` (input, electrical)
    - position 1: `din2` (input, electrical)
    - position 2: `din3` (input, electrical)
    - position 3: `din4` (input, electrical)
    - position 4: `rdy` (input, electrical)
    - position 5: `aout` (output, electrical)

## Public Parameter Contract

- `va_lx_dac_ideal_4b.vdd` defaults to `1.8`; valid range: finite; overrides vdd.
- `va_lx_dac_ideal_4b.vth` defaults to `0.9`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_READY_CLOCKED_SAMPLING`: restore: Only rising crossings of `rdy` through `vth` sample the four input bits; `aout` holds between ready events. Required traces: `time`, `rdy`, `din1`, `din2`, `din3`, `din4`, `aout`.
- `P_BINARY_BIT_ORDER`: restore: `din4` is the MSB and `din1` is the LSB of the sampled 4-bit unipolar code. Required traces: `time`, `rdy`, `din1`, `din2`, `din3`, `din4`, `aout`.
- `P_VDD_SCALED_DAC_OUTPUT`: restore: The sampled binary fraction is scaled by `vdd` and driven smoothly on `aout`. Required traces: `time`, `rdy`, `din1`, `din2`, `din3`, `din4`, `aout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `va_lx_dac_ideal_4b.va`.
Every supplied `.va` file is editable; do not add or omit files.
