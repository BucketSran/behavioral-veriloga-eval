# Reset Release Sequencer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `reset_release_sequencer.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `reset_release_sequencer.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `reset_release_sequencer.final_stage` defaults to `3`; valid range: finite; overrides final_stage.
- `reset_release_sequencer.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIALIZE_THE_INTERNAL_STAGE_COUNT_AND`: restore: Initialize the internal stage count and all observables to zero. On each rising clock crossing, clear the stage count when `rst` is high, `supply_ok <= vth`, or `bias_ok <= vth`. Otherwise increment the stage count by one until it reaches `final_stage`. Required traces: `time`, `bias_ok`, `clk`, `progress`, `ready`, `rst`, `stage1`, `stage2`, `supply_ok`.
- `P_AFTER_UPDATING_THE_STAGE_COUNT_DRIVE`: restore: After updating the stage count, drive `stage1 = vhi` when `stage_count >= 1`, `stage2 = vhi` when `stage_count >= 2`, and `ready = vhi` when `stage_count >= final_stage`; otherwise drive each of those observables to `0 V`. Drive `progress = vhi * clip01(stage_count / final_stage)`. Hold the last observable values between rising clock crossings. Required traces: `time`, `bias_ok`, `clk`, `progress`, `ready`, `rst`, `stage1`, `stage2`, `supply_ok`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `reset_release_sequencer.va`.
Every supplied `.va` file is editable; do not add or omit files.
