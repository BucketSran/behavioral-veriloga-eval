# Iterative ISAR DAC Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Iterative ISAR DAC` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `iterative_isar_dac.va`:
  - Module `iterative_isar_dac` (entry)
    - position 0: `dcmp` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `vdac` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `iterative_isar_dac` as `XDUT` with ordered public binding: dcmp=dcmp, rst=rst, clk=clk, vdac=vdac.

## Public Parameter Contract

- `iterative_isar_dac.vth` defaults to `0.5`; valid range: finite; overrides vth.
- `iterative_isar_dac.tr` defaults to `100p`; valid range: finite; overrides tr.
- `iterative_isar_dac.range` defaults to `0.1`; valid range: finite; overrides range.
- `iterative_isar_dac.lsb` defaults to `10u`; valid range: finite; overrides lsb.
- `iterative_isar_dac.radix` defaults to `2`; valid range: finite; overrides radix.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_INITIAL_SEARCH_STATE`: exercise and make observable: At initialization and reset, `vdac` returns to zero and the search step returns to `range`. Required traces: `time`, `rst`, `vdac`.
- `P_COMPARATOR_POLARITY_UPDATE`: exercise and make observable: On each rising `clk` crossing while active, `dcmp > vth` steps `vdac` in the specified comparator-driven direction and low decisions step the opposite way. Required traces: `time`, `clk`, `dcmp`, `vdac`.
- `P_RADIX_STEP_REDUCTION`: exercise and make observable: The search step is divided by the public radix after each active comparison until it reaches the LSB limit. Required traces: `time`, `clk`, `dcmp`, `rst`, `vdac`.
- `P_HELD_DAC_OUTPUT`: exercise and make observable: `vdac` holds the current iterative search value between reset and qualifying clock events. Required traces: `time`, `clk`, `rst`, `vdac`.

The required trace names are: `time`, `dcmp`, `rst`, `clk`, `vdac`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
