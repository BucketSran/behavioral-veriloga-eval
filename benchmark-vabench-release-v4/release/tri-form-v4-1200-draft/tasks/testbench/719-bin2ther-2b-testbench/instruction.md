# Bin2ther 2b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Bin2ther 2b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bin2ther_2b.va`:
  - Module `bin2ther_2b` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `gnd` (input, electrical)
    - position 2: `b1` (input, electrical)
    - position 3: `b0` (input, electrical)
    - position 4: `t0` (output, electrical)
    - position 5: `t1` (output, electrical)
    - position 6: `t2` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bin2ther_2b` as `XDUT` with ordered public binding: vdd=vdd, gnd=gnd, b1=b1, b0=b0, t0=t0, t1=t1, t2=t2.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INTERPRET_B1_AND_B0_RELATIVE_TO`: exercise and make observable: Interpret `b1` and `b0` relative to the local rail midpoint. Required traces: `time`, `b0`, `b1`, `gnd`, `t0`, `t1`, `t2`, `vdd`.
- `P_DRIVE_T0_AND_T1_HIGH_TOGETHER`: exercise and make observable: Drive `t0` and `t1` high together when `b1` is high. Required traces: `time`, `b0`, `b1`, `gnd`, `t0`, `t1`, `t2`, `vdd`.
- `P_DRIVE_T2_HIGH_WHEN_B0_IS`: exercise and make observable: Drive `t2` high when `b0` is high. Required traces: `time`, `b0`, `b1`, `gnd`, `t0`, `t1`, `t2`, `vdd`.
- `P_DRIVE_EACH_LOW_OUTPUT_TO_THE`: exercise and make observable: Drive each low output to the local `gnd` rail and each high output to the local `vdd` rail. Required traces: `time`, `b0`, `b1`, `gnd`, `t0`, `t1`, `t2`, `vdd`.

The required trace names are: `time`, `b0`, `b1`, `gnd`, `t0`, `t1`, `t2`, `vdd`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
