# Ideal Differential Opamp Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Ideal Differential Opamp` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ideal_differential_opamp.va`:
  - Module `ideal_differential_opamp` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `voutp` (output, electrical)
    - position 3: `voutn` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ideal_differential_opamp` as `XDUT` with ordered public binding: vinp=vinp, vinn=vinn, voutp=voutp, voutn=voutn.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FIXED_COMMON_MODE`: exercise and make observable: Maintain both outputs symmetric around a fixed 0.5 V common mode. Required traces: `time`, `voutp`, `voutn`.
- `P_DIFFERENTIAL_GAIN_FOUR`: exercise and make observable: Make the differential output `V(voutp) - V(voutn)` equal to four times `V(vinp, vinn)`. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`.
- `P_OUTPUT_POLARITY`: exercise and make observable: For positive `V(vinp, vinn)`, drive `voutp` above common mode and `voutn` below common mode. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`.

The required trace names are: `time`, `vinn`, `vinp`, `voutn`, `voutp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
