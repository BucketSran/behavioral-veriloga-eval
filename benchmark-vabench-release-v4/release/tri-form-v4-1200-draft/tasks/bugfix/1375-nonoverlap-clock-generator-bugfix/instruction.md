# Non-overlapping Clock Generator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `nonoverlap_clock_generator.va`:
  - Module `nonoverlap_clock_generator` (entry)
    - position 0: `clk_in` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `phi1` (output, electrical)
    - position 4: `phi2` (output, electrical)
    - position 5: `deadtime_metric` (output, electrical)
    - position 6: `valid` (output, electrical)

## Public Parameter Contract

- `nonoverlap_clock_generator.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `nonoverlap_clock_generator.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `nonoverlap_clock_generator.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `nonoverlap_clock_generator.dead_ticks` defaults to `5 from [1:100]`; valid range: finite; overrides dead_ticks.
- `nonoverlap_clock_generator.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.
- `nonoverlap_clock_generator.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_OR_A_LOW_ENABLE_CLEARS`: restore: Reset or a low `enable` clears both phases, `deadtime_metric`, and `valid`. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_A_RISING_CLK_IN_REQUEST_EVENTUALLY`: restore: A rising `clk_in` request eventually enables `phi1`; a falling `clk_in` request eventually enables `phi2`. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_DURING_EACH_HANDOFF_BOTH_PHI1_AND`: restore: During each handoff, both `phi1` and `phi2` remain low for the configured dead-time interval. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_PHI1_AND_PHI2_MUST_NEVER_BE`: restore: `phi1` and `phi2` must never be high at the same time. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_DEADTIME_METRIC_IS_HIGH_ONLY_WHILE`: restore: `deadtime_metric` is high only while a pending phase request is in the enforced both-low interval. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.
- `P_VALID_BECOMES_HIGH_AFTER_THE_FIRST`: restore: `valid` becomes high after the first enabled handoff completes and remains high until reset or disable. Required traces: `time`, `clk_in`, `rst`, `enable`, `phi1`, `phi2`, `deadtime_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `nonoverlap_clock_generator.va`.
Every supplied `.va` file is editable; do not add or omit files.
