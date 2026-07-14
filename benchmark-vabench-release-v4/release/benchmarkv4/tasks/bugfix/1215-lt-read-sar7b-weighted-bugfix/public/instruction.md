# LT Read SAR7B Weighted Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `lt_read_sar7b_weighted.va`:
  - Module `lt_read_sar7b_weighted` (entry)
    - position 0: `d0` (input, electrical)
    - position 1: `d1` (input, electrical)
    - position 2: `d2` (input, electrical)
    - position 3: `d3` (input, electrical)
    - position 4: `d4` (input, electrical)
    - position 5: `d5` (input, electrical)
    - position 6: `d6` (input, electrical)
    - position 7: `d7` (input, electrical)
    - position 8: `vout` (output, electrical)
    - position 9: `gnd` (input, electrical)

## Public Parameter Contract

- `lt_read_sar7b_weighted.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `lt_read_sar7b_weighted.vref` defaults to `0.9`; valid range: finite; overrides vref.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CONTINUOUSLY_DRIVE`: restore: Continuously drive: Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `gnd`, `vout`.
- `P_TEXT_VOUT_VREF_VREF_D7_D6`: restore: ```text vout = -vref + vref * (d7 + d6/2 + d5/4 + d4/8 + d3/16 + d2/32 + d1/64 + d0/128) ``` Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `gnd`, `vout`.
- `P_WHERE_EACH_D_TERM_IS_1`: restore: where each `d` term is `1` when the corresponding input voltage is above `vth` and `0` otherwise. Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `gnd`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `lt_read_sar7b_weighted.va`.
Every supplied `.va` file is editable; do not add or omit files.
