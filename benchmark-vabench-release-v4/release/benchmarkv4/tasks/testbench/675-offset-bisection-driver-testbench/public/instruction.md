# Offset Bisection Driver Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Offset Bisection Driver` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `offset_bisection_driver.va`:
  - Module `offset_bisection_driver` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vout` (input, electrical)
    - position 2: `vcm` (input, electrical)
    - position 3: `vinp` (output, electrical)
    - position 4: `vinn` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `offset_bisection_driver` as `XDUT` with ordered public binding: clk=clk, vout=vout, vcm=vcm, vinp=vinp, vinn=vinn.

## Public Parameter Contract

- `offset_bisection_driver.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `offset_bisection_driver.step_initial` defaults to `10m`; valid range: finite; overrides step_initial.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_BISECTION_INITIAL_STATE`: exercise and make observable: The differential residue initializes to zero, the step initializes to `step_initial`, and the previous decision polarity initializes to the low-decision direction. Required traces: `time`, `clk`, `vout`, `vcm`, `vinp`, `vinn`.
- `P_FALLING_CLOCK_DECISION_UPDATE`: exercise and make observable: On each falling `clk` crossing, sample `vout` and update the residue using the specified comparator polarity. Required traces: `time`, `clk`, `vout`, `vinp`, `vinn`.
- `P_SIGN_CHANGE_STEP_HALVING`: exercise and make observable: The bisection step halves when the sampled decision polarity changes. Required traces: `time`, `clk`, `vout`, `vinp`, `vinn`.
- `P_VCM_CENTERED_DIFFERENTIAL_DRIVE`: exercise and make observable: `vinp` and `vinn` remain centered around `vcm` with half of the differential residue on each side. Required traces: `time`, `vcm`, `vinp`, `vinn`.

The required trace names are: `time`, `clk`, `vout`, `vcm`, `vinp`, `vinn`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
