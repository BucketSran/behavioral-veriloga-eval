# Strongarm Style Latch Comparator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cmp_strongarm.va`:
  - Module `cmp_strongarm` (entry)
    - position 0: `CLK` (input, electrical)
    - position 1: `VINN` (input, electrical)
    - position 2: `VINP` (input, electrical)
    - position 3: `DCMPN` (output, electrical)
    - position 4: `DCMPP` (output, electrical)
    - position 5: `LP` (output, electrical)
    - position 6: `LM` (output, electrical)
    - position 7: `VSS` (input, electrical)
    - position 8: `VDD` (input, electrical)

## Public Parameter Contract

- `cmp_strongarm.td_cmp` defaults to `0.0` s; valid range: td_cmp >= 0; sets comparator output delay.
- `cmp_strongarm.voffset` defaults to `0.0` V; valid range: finite real; is subtracted from the sampled VINP minus VINN differential.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_AND_FALLING_RESET`: restore: All decision and latch monitor outputs initialize low and return low after each falling clock crossing. Required traces: `time`, `clk`, `out_n`, `out_p`, `lp`, `lm`.
- `P_POSITIVE_DECISION`: restore: A rising clock crossing with VINP minus VINN minus voffset positive latches DCMPP and LP high while DCMPN and LM remain low. Required traces: `time`, `clk`, `vinp`, `vinn`, `out_p`, `out_n`, `lp`, `lm`, `vdd`, `vss`.
- `P_NEGATIVE_DECISION`: restore: A rising clock crossing with VINP minus VINN minus voffset negative latches DCMPN and LM high while DCMPP and LP remain low. Required traces: `time`, `clk`, `vinp`, `vinn`, `out_p`, `out_n`, `lp`, `lm`, `vdd`, `vss`.
- `P_ZERO_DIFFERENTIAL`: restore: An exactly zero effective differential sampled at a rising clock crossing leaves both complementary decision states low. Required traces: `time`, `clk`, `vinp`, `vinn`, `out_p`, `out_n`, `lp`, `lm`.
- `P_LATCH_HOLD`: restore: The sampled decision is held between clock events and does not track input changes while the clock remains high. Required traces: `time`, `clk`, `vinp`, `vinn`, `out_p`, `out_n`, `lp`, `lm`.

## Modeling Constraints

- Use the local rail midpoint as the clock threshold.
- Update discrete decision state only on initialization and clock crossings, and drive smoothed voltage contributions outside event blocks.
- Use voltage contributions only; do not use current contributions, ddt(), idt(), validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cmp_strongarm.va`.
Every supplied `.va` file is editable; do not add or omit files.
