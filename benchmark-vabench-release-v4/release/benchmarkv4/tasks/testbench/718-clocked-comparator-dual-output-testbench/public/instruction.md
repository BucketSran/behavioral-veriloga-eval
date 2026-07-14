# Clocked Comparator Dual Output Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clocked Comparator Dual Output` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `clocked_comparator_dual_output.va`:
  - Module `clocked_comparator_dual_output` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `vinp` (input, electrical)
    - position 3: `outn` (output, electrical)
    - position 4: `outp` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `clocked_comparator_dual_output` as `XDUT` with ordered public binding: clk=clk, vinn=vinn, vinp=vinp, outn=outn, outp=outp.

## Public Parameter Contract

- `clocked_comparator_dual_output.vdd` defaults to `1.0`; valid range: finite; overrides vdd.
- `clocked_comparator_dual_output.td_cmp` defaults to `100p`; valid range: finite; overrides td_cmp.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIALIZE_BOTH_DECISION_OUTPUTS_LOW`: exercise and make observable: Initialize both decision outputs low. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_WHENEVER_CLK_FALLS_THROUGH_VDD_2`: exercise and make observable: Whenever `clk` falls through `vdd/2`, reset both outputs low. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_WHENEVER_CLK_RISES_THROUGH_VDD_2`: exercise and make observable: Whenever `clk` rises through `vdd/2`, latch a differential decision. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_DRIVE_OUTP_HIGH_AND_OUTN_LOW`: exercise and make observable: Drive `outp` high and `outn` low for `vinp > vinn`. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_DRIVE_OUTN_HIGH_AND_OUTP_LOW`: exercise and make observable: Drive `outn` high and `outp` low for `vinp < vinn`. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.
- `P_DRIVE_BOTH_OUTPUTS_LOW_FOR_AN`: exercise and make observable: Drive both outputs low for an equal-input decision. Required traces: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.

The required trace names are: `time`, `clk`, `outn`, `outp`, `vinn`, `vinp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
