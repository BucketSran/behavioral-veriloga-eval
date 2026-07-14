# VCO Phase Integrator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `VCO Phase Integrator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `vco_phase_integrator.va`:
  - Module `vco_phase_integrator` (entry)
    - position 0: `vctrl` (input, electrical)
    - position 1: `phase` (output, electrical)
    - position 2: `clk` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `vco_phase_integrator` as `XDUT` with ordered public binding: vctrl=vctrl, phase=phase, clk=clk.

## Public Parameter Contract

- `vco_phase_integrator.tr` defaults to `2e-10` s; valid range: tr > 0; sets phase and clock transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_PERIODIC_PHASE_UPDATE`: exercise and make observable: Phase state updates on the public 1 ns periodic schedule by 0.03 plus 0.09 times vctrl. Required traces: `time`, `vctrl`, `phase`.
- `P_WRAPPED_PHASE_RANGE`: exercise and make observable: The observable phase remains in the normalized range from 0 inclusive to 1 exclusive. Required traces: `time`, `phase`.
- `P_WRAP_TOGGLES_CLOCK`: exercise and make observable: Each phase wrap by one cycle toggles the voltage-coded clock between 0 V and 0.9 V. Required traces: `time`, `phase`, `clk`.
- `P_CONTROLLED_EDGE_RATE`: exercise and make observable: A sustained higher vctrl produces more clock toggles over the same observation interval than a sustained lower vctrl. Required traces: `time`, `vctrl`, `clk`.

The required trace names are: `time`, `vctrl`, `phase`, `clk`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
