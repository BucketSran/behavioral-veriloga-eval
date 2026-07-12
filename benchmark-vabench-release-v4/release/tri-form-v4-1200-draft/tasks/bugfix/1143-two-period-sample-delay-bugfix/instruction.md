# Two Period Sample Delay Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `two_period_sample_delay.va`:
  - Module `two_period_sample_delay` (entry)
    - position 0: `update` (input, electrical)
    - position 1: `ain` (input, electrical)
    - position 2: `aout` (output, electrical)

## Public Parameter Contract

- `two_period_sample_delay.vth` defaults to `0.5`; valid range: finite; overrides vth.
- `two_period_sample_delay.tr` defaults to `50p`; valid range: finite; overrides tr.
- `two_period_sample_delay.init` defaults to `0.0`; valid range: finite; overrides init.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TWO_PERIOD_DELAY_STATE`: restore: On each rising `update` crossing through `vth`, `aout` updates to the value sampled on the previous update event, then captures the current `ain` for the next event. Required traces: `time`, `ain`, `aout`, `update`.
- `P_INITIAL_OUTPUT_VALUE`: restore: Before enough update events have occurred, the retained samples and `aout` start from `init`. Required traces: `time`, `ain`, `aout`, `update`.
- `P_OUTPUT_GAIN_AND_HOLD`: restore: The held `aout` value matches the delayed sample amplitude without gain scaling between update events. Required traces: `time`, `ain`, `aout`, `update`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `two_period_sample_delay.va`.
Every supplied `.va` file is editable; do not add or omit files.
