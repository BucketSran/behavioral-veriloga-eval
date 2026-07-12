# Reset Release Sequencer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Reset Release Sequencer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `reset_release_sequencer.va`:
  - Module `reset_release_sequencer` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `supply_ok` (input, electrical)
    - position 3: `bias_ok` (input, electrical)
    - position 4: `stage1` (output, electrical)
    - position 5: `stage2` (output, electrical)
    - position 6: `ready` (output, electrical)
    - position 7: `progress` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `reset_release_sequencer` as `XDUT` with ordered public binding: clk=clk, rst=rst, supply_ok=supply_ok, bias_ok=bias_ok, stage1=stage1, stage2=stage2, ready=ready, progress=progress.

## Public Parameter Contract

- `reset_release_sequencer.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `reset_release_sequencer.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `reset_release_sequencer.final_stage` defaults to `3`; valid range: finite; overrides final_stage.
- `reset_release_sequencer.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIALIZE_THE_INTERNAL_STAGE_COUNT_AND`: exercise and make observable: Initialize the internal stage count and all observables to zero. On each rising clock crossing, clear the stage count when `rst` is high, `supply_ok <= vth`, or `bias_ok <= vth`. Otherwise increment the stage count by one until it reaches `final_stage`. Required traces: `time`, `bias_ok`, `clk`, `progress`, `ready`, `rst`, `stage1`, `stage2`, `supply_ok`.
- `P_AFTER_UPDATING_THE_STAGE_COUNT_DRIVE`: exercise and make observable: After updating the stage count, drive `stage1 = vhi` when `stage_count >= 1`, `stage2 = vhi` when `stage_count >= 2`, and `ready = vhi` when `stage_count >= final_stage`; otherwise drive each of those observables to `0 V`. Drive `progress = vhi * clip01(stage_count / final_stage)`. Hold the last observable values between rising clock crossings. Required traces: `time`, `bias_ok`, `clk`, `progress`, `ready`, `rst`, `stage1`, `stage2`, `supply_ok`.

The required trace names are: `time`, `bias_ok`, `clk`, `progress`, `ready`, `rst`, `stage1`, `stage2`, `supply_ok`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
