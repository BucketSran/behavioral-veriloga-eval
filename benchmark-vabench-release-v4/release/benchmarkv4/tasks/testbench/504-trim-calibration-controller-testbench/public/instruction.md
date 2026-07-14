# Trim Calibration Controller Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Trim Calibration Controller` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `cdac_calibration.va`:
  - Module `cdac_calibration` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `err` (input, electrical)
    - position 3: `trim` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cdac_calibration` as `XDUT` with ordered public binding: clk=clk, rst=rst, err=err, trim=trim.

## Public Parameter Contract

- `cdac_calibration.vth` defaults to `0.45` V; valid range: vth > 0; sets clk, rst, and err decision threshold.
- `cdac_calibration.tr` defaults to `5e-10` s; valid range: tr > 0; sets trim transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_AND_RESET`: exercise and make observable: trim initializes to 0.45 V and returns to 0.45 V on a rising clk edge while rst is high. Required traces: `time`, `clk`, `rst`, `trim`.
- `P_CLOCKED_STEP`: exercise and make observable: Each rising clk edge outside reset adds 0.06 V for high err and subtracts 0.06 V for low err. Required traces: `time`, `clk`, `rst`, `err`, `trim`.
- `P_TRIM_CLAMP`: exercise and make observable: trim is clamped to the inclusive 0.05 V to 0.85 V range. Required traces: `time`, `trim`.
- `P_CLOCKED_HOLD`: exercise and make observable: trim holds its state between rising clk updates. Required traces: `time`, `clk`, `trim`.

The required trace names are: `time`, `clk`, `rst`, `err`, `trim`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
