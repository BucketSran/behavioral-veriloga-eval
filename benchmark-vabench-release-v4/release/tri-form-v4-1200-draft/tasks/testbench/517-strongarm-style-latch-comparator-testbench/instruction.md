# Strongarm Style Latch Comparator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Strongarm Style Latch Comparator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cmp_strongarm` as `XDUT` with ordered public binding: CLK=clk, VINN=vinn, VINP=vinp, DCMPN=dcmpn, DCMPP=dcmpp, LP=lp, LM=lm, VSS=vss, VDD=vdd.

## Public Parameter Contract

- `cmp_strongarm.td_cmp` defaults to `0.0` s; valid range: td_cmp >= 0; sets comparator output delay.
- `cmp_strongarm.voffset` defaults to `0.0` V; valid range: finite real; is subtracted from the sampled VINP minus VINN differential.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_AND_FALLING_RESET`: exercise and make observable: All decision and latch monitor outputs initialize low and return low after each falling clock crossing. Required traces: `time`, `clk`, `out_n`, `out_p`, `lp`, `lm`.
- `P_POSITIVE_DECISION`: exercise and make observable: A rising clock crossing with VINP minus VINN minus voffset positive latches DCMPP and LP high while DCMPN and LM remain low. Required traces: `time`, `clk`, `vinp`, `vinn`, `out_p`, `out_n`, `lp`, `lm`, `vdd`, `vss`.
- `P_NEGATIVE_DECISION`: exercise and make observable: A rising clock crossing with VINP minus VINN minus voffset negative latches DCMPN and LM high while DCMPP and LP remain low. Required traces: `time`, `clk`, `vinp`, `vinn`, `out_p`, `out_n`, `lp`, `lm`, `vdd`, `vss`.
- `P_ZERO_DIFFERENTIAL`: exercise and make observable: An exactly zero effective differential sampled at a rising clock crossing leaves both complementary decision states low. Required traces: `time`, `clk`, `vinp`, `vinn`, `out_p`, `out_n`, `lp`, `lm`.
- `P_LATCH_HOLD`: exercise and make observable: The sampled decision is held between clock events and does not track input changes while the clock remains high. Required traces: `time`, `clk`, `vinp`, `vinn`, `out_p`, `out_n`, `lp`, `lm`.

The required trace names are: `time`, `clk`, `vinn`, `vinp`, `out_n`, `out_p`, `lp`, `lm`, `vss`, `vdd`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
