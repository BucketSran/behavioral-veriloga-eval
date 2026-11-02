# Event Reacquire Lock Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Event Reacquire Lock Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `event_reacquire_lock_detector.va`:
  - Module `event_reacquire_lock_detector` (entry)
    - position 0: `ref_clk` (input, electrical)
    - position 1: `fb_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `lock` (output, electrical)
    - position 4: `phase_metric` (output, electrical)
    - position 5: `state_mon` (output, electrical)

Stable public Spectre binding:

The submitted `testbench.scs` must use the supplied DUT through this public binding:

- Include path: `./dut/event_reacquire_lock_detector.va`
- DUT instance: `XDUT (ref_clk fb_clk rst lock phase_metric state_mon) event_reacquire_lock_detector lock_window=180p`
- Required saved public traces: `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`
- Use one bounded transient analysis with a finite positive stop time.

You must design the stimulus yourself. Save traces as bare public signal names
(for example `clk`, not suffixed or hierarchical forms such as `clk:V` or
`XDUT.clk`). Do not redefine the DUT, drive DUT output nets, save
hierarchical/private nodes, or use checker/gold/internal files.

## Public Parameter Contract

- `event_reacquire_lock_detector.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `event_reacquire_lock_detector.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `event_reacquire_lock_detector.lock_window` defaults to `180p`; valid range: finite; overrides lock_window.
- `event_reacquire_lock_detector.metric_fullscale` defaults to `600p`; valid range: finite; overrides metric_fullscale.
- `event_reacquire_lock_detector.lock_count` defaults to `3`; valid range: finite; overrides lock_count.
- `event_reacquire_lock_detector.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RECORD_REFERENCE_CLOCK_RISING_EDGE_TIME`: exercise and make observable: Record reference clock rising-edge time and evaluate feedback clock rising edges against it. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.
- `P_REQUIRE_CONSECUTIVE_IN_WINDOW_FEEDBACK_EDGE`: exercise and make observable: Require consecutive in-window feedback edge errors before lock asserts. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.
- `P_CLEAR_LOCK_STATE_AND_PROGRESS_WHEN`: exercise and make observable: Clear lock state and progress when reset rises or is sampled high. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.
- `P_EXPOSE_PHASE_METRIC_AND_STATE_MON`: exercise and make observable: Expose phase_metric and state_mon as bounded voltage-coded observables. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.
- `P_USE_EVENT_BODY_STATE_UPDATES_PLUS`: exercise and make observable: Use event-body state updates plus local analog helper functions rather than user task/endtask syntax. Required traces: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.


The following canonical public behavior is normative for this derived form:

- Record reference clock rising-edge time and evaluate feedback clock rising edges against it.
- Require consecutive in-window feedback edge errors before lock asserts.
- Clear lock state and progress when reset rises or is sampled high.
- Expose phase_metric and state_mon as bounded voltage-coded observables.
- Use event-body state updates plus local analog helper functions rather than user task/endtask syntax.


The required trace names are: `time`, `fb_clk`, `lock`, `phase_metric`, `ref_clk`, `rst`, `state_mon`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.

- phase_error / metric_fullscale

- good_count / lock_count

- phase_error <= lock_window
