# Clocked Comparator Dual Output Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clocked_comparator_dual_output.va`:
  - Module `clocked_comparator_dual_output` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `vinp` (input, electrical)
    - position 3: `outn` (output, electrical)
    - position 4: `outp` (output, electrical)

## Public Parameter Contract

- `clocked_comparator_dual_output.vdd` defaults to `1.0`; valid range: finite; overrides vdd.
- `clocked_comparator_dual_output.td_cmp` defaults to `100p`; valid range: finite; overrides td_cmp.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIALIZE_BOTH_DECISION_OUTPUTS_LOW`: restore: Initialize both decision outputs low. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_WHENEVER_CLK_FALLS_THROUGH_VDD_2`: restore: Whenever `clk` falls through `vdd/2`, reset both outputs low. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_WHENEVER_CLK_RISES_THROUGH_VDD_2`: restore: Whenever `clk` rises through `vdd/2`, latch a differential decision. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_DRIVE_OUTP_HIGH_AND_OUTN_LOW`: restore: Drive `outp` high and `outn` low for `vinp > vinn`. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_DRIVE_OUTN_HIGH_AND_OUTP_LOW`: restore: Drive `outn` high and `outp` low for `vinp < vinn`. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_DRIVE_BOTH_OUTPUTS_LOW_FOR_AN`: restore: Drive both outputs low for an equal-input decision. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clocked_comparator_dual_output.va`.
Every supplied `.va` file is editable; do not add or omit files.
