# SAR DAS Logic 6b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sar_das_logic_6b.va`:
  - Module `sar_das_logic_6b` (entry)
    - position 0: `clk_sampling` (input, electrical)
    - position 1: `clk_sar` (input, electrical)
    - position 2: `vcomp` (input, electrical)
    - position 3: `d1` (output, electrical)
    - position 4: `d2` (output, electrical)
    - position 5: `d3` (output, electrical)
    - position 6: `d4` (output, electrical)
    - position 7: `d5` (output, electrical)
    - position 8: `d6` (output, electrical)
    - position 9: `db1` (output, electrical)
    - position 10: `db2` (output, electrical)
    - position 11: `db3` (output, electrical)
    - position 12: `db4` (output, electrical)
    - position 13: `db5` (output, electrical)
    - position 14: `db6` (output, electrical)
    - position 15: `co` (output, electrical)
    - position 16: `cob` (output, electrical)

## Public Parameter Contract

- `sar_das_logic_6b.tde` defaults to `50p`; valid range: finite; overrides tde.
- `sar_das_logic_6b.tdc` defaults to `50p`; valid range: finite; overrides tdc.
- `sar_das_logic_6b.vdd` defaults to `1.1`; valid range: finite; overrides vdd.
- `sar_das_logic_6b.vcm` defaults to `0.55`; valid range: finite; overrides vcm.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SAMPLING_RESET_CONVERSION_STATE`: restore: A rising `clk_sampling` transition clears controls and pulses, and a falling transition arms the SAR conversion sequence. Required traces: `time`, `clk_sampling`, `clk_sar`, `co`, `cob`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `db1`, `db2`, `db3`, `db4`, `db5`, `db6`, `vcomp`.
- `P_SAR_COMPARATOR_POLARITY`: restore: Each rising `clk_sar` transition compares `vcomp` to `vcm` and drives `co/cob` with the declared polarity. Required traces: `time`, `clk_sampling`, `clk_sar`, `co`, `cob`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `db1`, `db2`, `db3`, `db4`, `db5`, `db6`, `vcomp`.
- `P_SIX_BIT_DECISION_SEQUENCE`: restore: The SAR decisions update `d6..d1` in the declared order through the conversion. Required traces: `time`, `clk_sampling`, `clk_sar`, `co`, `cob`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `db1`, `db2`, `db3`, `db4`, `db5`, `db6`, `vcomp`.
- `P_CONTROL_OUTPUT_LEVELS`: restore: Decision pulses and bit-control outputs use valid voltage-coded low/high levels. Required traces: `time`, `clk_sampling`, `clk_sar`, `co`, `cob`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `db1`, `db2`, `db3`, `db4`, `db5`, `db6`, `vcomp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sar_das_logic_6b.va`.
Every supplied `.va` file is editable; do not add or omit files.
