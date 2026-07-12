# LT Read SAR7B Weighted Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `LT Read SAR7B Weighted` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `lt_read_sar7b_weighted` as `XDUT` with ordered public binding: d0=d0, d1=d1, d2=d2, d3=d3, d4=d4, d5=d5, d6=d6, d7=d7, vout=vout, gnd=gnd.

## Public Parameter Contract

- `lt_read_sar7b_weighted.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `lt_read_sar7b_weighted.vref` defaults to `0.9`; valid range: finite; overrides vref.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CONTINUOUSLY_DRIVE`: exercise and make observable: Continuously drive: Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `gnd`, `vout`.
- `P_TEXT_VOUT_VREF_VREF_D7_D6`: exercise and make observable: ```text vout = -vref + vref * (d7 + d6/2 + d5/4 + d4/8 + d3/16 + d2/32 + d1/64 + d0/128) ``` Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `gnd`, `vout`.
- `P_WHERE_EACH_D_TERM_IS_1`: exercise and make observable: where each `d` term is `1` when the corresponding input voltage is above `vth` and `0` otherwise. Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `gnd`, `vout`.

The required trace names are: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `gnd`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
