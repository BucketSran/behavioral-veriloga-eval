# Divide By Two Toggle Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Divide By Two Toggle` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `divide_by_two_toggle.va`:
  - Module `divide_by_two_toggle` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `divide_by_two_toggle` as `XDUT` with ordered public binding: clk=clk, out=out.

## Public Parameter Contract

- `divide_by_two_toggle.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `divide_by_two_toggle.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `divide_by_two_toggle.tdel` defaults to `10p`; valid range: finite; overrides tdel.
- `divide_by_two_toggle.tr` defaults to `10p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIALIZE_THE_INTERNAL_DIVIDER_STATE_LOW`: exercise and make observable: Initialize the internal divider state low. Required traces: `time`, `clk`, `out`.
- `P_TOGGLE_THE_STATE_ON_EVERY_RISING`: exercise and make observable: Toggle the state on every rising `clk` crossing through `vth`. Required traces: `time`, `clk`, `out`.
- `P_DRIVE_OUT_LOW_WHEN_THE_STATE`: exercise and make observable: Drive `out` low when the state is low and to `vdd` when the state is high. Required traces: `time`, `clk`, `out`.
- `P_THE_FIRST_VALID_RISING_EDGE_DRIVES`: exercise and make observable: The first valid rising edge drives `out` high. Required traces: `time`, `clk`, `out`.

The required trace names are: `time`, `clk`, `out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
