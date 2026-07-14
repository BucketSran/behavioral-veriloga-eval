# Event Reacquire Lock Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `event_reacquire_lock_detector.va`:
  - Module `event_reacquire_lock_detector` (entry)
    - position 0: `ref_clk` (input, electrical)
    - position 1: `fb_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `lock` (output, electrical)
    - position 4: `phase_metric` (output, electrical)
    - position 5: `state_mon` (output, electrical)

## Public Parameter Contract

- `event_reacquire_lock_detector.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `event_reacquire_lock_detector.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `event_reacquire_lock_detector.lock_window` defaults to `180p`; valid range: finite; overrides lock_window.
- `event_reacquire_lock_detector.metric_fullscale` defaults to `600p`; valid range: finite; overrides metric_fullscale.
- `event_reacquire_lock_detector.lock_count` defaults to `3`; valid range: finite; overrides lock_count.
- `event_reacquire_lock_detector.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RECORD_REFERENCE_CLOCK_RISING_EDGE_TIME`: restore: Record reference clock rising-edge time and evaluate feedback clock rising edges against it. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.
- `P_REQUIRE_CONSECUTIVE_IN_WINDOW_FEEDBACK_EDGE`: restore: Require consecutive in-window feedback edge errors before lock asserts. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.
- `P_CLEAR_LOCK_STATE_AND_PROGRESS_WHEN`: restore: Clear lock state and progress when reset rises or is sampled high. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.
- `P_EXPOSE_PHASE_METRIC_AND_STATE_MON`: restore: Expose phase_metric and state_mon as bounded voltage-coded observables. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.
- `P_USE_EVENT_BODY_STATE_UPDATES_PLUS`: restore: Use event-body state updates plus local analog helper functions rather than user task/endtask syntax. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `event_reacquire_lock_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
