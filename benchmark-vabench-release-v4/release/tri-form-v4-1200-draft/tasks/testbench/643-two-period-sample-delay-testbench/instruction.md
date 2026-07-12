# Two Period Sample Delay Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Two Period Sample Delay` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `two_period_sample_delay.va`:
  - Module `two_period_sample_delay` (entry)
    - position 0: `update` (input, electrical)
    - position 1: `ain` (input, electrical)
    - position 2: `aout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `two_period_sample_delay` as `XDUT` with ordered public binding: update=update, ain=ain, aout=aout.

## Public Parameter Contract

- `two_period_sample_delay.vth` defaults to `0.5`; valid range: finite; overrides vth.
- `two_period_sample_delay.tr` defaults to `50p`; valid range: finite; overrides tr.
- `two_period_sample_delay.init` defaults to `0.0`; valid range: finite; overrides init.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_TWO_PERIOD_DELAY_STATE`: exercise and make observable: On each rising `update` crossing through `vth`, `aout` updates to the value sampled on the previous update event, then captures the current `ain` for the next event. Required traces: `time`, `ain`, `aout`, `update`.
- `P_INITIAL_OUTPUT_VALUE`: exercise and make observable: Before enough update events have occurred, the retained samples and `aout` start from `init`. Required traces: `time`, `ain`, `aout`, `update`.
- `P_OUTPUT_GAIN_AND_HOLD`: exercise and make observable: The held `aout` value matches the delayed sample amplitude without gain scaling between update events. Required traces: `time`, `ain`, `aout`, `update`.

The required trace names are: `time`, `ain`, `aout`, `update`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
