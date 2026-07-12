# LT Readout SAR4 Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `lt_readout_sar4.va`:
  - Module `lt_readout_sar4` (entry)
    - position 0: `d0` (input, electrical)
    - position 1: `d1` (input, electrical)
    - position 2: `d2` (input, electrical)
    - position 3: `d3` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `gnd` (input, electrical)

## Public Parameter Contract

- `lt_readout_sar4.vth` defaults to `0.9`; valid range: finite; overrides vth.
- `lt_readout_sar4.vref` defaults to `1.8`; valid range: finite; overrides vref.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CONTINUOUSLY_DECODE_D0_D3_AS_AN`: restore: Continuously decode `d0..d3` as an unsigned binary code with `d0` as LSB and `d3` as MSB. Drive `vout` to the readout level `code * vref / 16`. The output should update when the voltage-coded input bits cross the threshold. Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `gnd`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `lt_readout_sar4.va`.
Every supplied `.va` file is editable; do not add or omit files.
