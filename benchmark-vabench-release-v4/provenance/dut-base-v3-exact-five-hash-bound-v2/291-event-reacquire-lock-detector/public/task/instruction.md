# Event Reacquire Lock Detector

## Task Contract

Build a Spectre-compatible voltage-domain behavioral model for PLL/clock timing monitor that detects lock, reset clearing, and reacquisition from event-ordered ref/fb edges.

This is a DUT source task. Implement only the `event_reacquire_lock_detector` module; no external validation code, transistor devices, or extra helper module is part of the requested artifact.

## Public Verilog-A Interface

```verilog
module event_reacquire_lock_detector(ref_clk, fb_clk, rst, lock, phase_metric, state_mon);
```

## Public Parameter Contract

- `parameter real vth = 0.45`.
- `parameter real vhi = 0.9`.
- `parameter real lock_window = 180p`.
- `parameter real metric_fullscale = 600p`.
- `parameter integer lock_count = 3`.
- `parameter real tr = 60p`.

## Required Behavior

- On each rising `ref_clk` crossing, record `last_ref_time = $abstime`. On each rising `fb_clk` crossing while reset is low, let `phase_error = abs($abstime - last_ref_time)`; before any reference edge, use `metric_fullscale` as the phase error.
- A feedback edge with a recorded reference and `phase_error <= lock_window` increments the consecutive-good count, capped at `lock_count`; any other feedback edge resets the count to zero. Drive `lock = vhi` exactly when the count reaches `lock_count`.
- Clear the consecutive-good count, `lock`, `phase_metric`, and `state_mon` when reset rises or when a feedback edge samples reset high.
- After each reset-low feedback edge, drive `phase_metric = vhi * clip01(phase_error / metric_fullscale)` and `state_mon = vhi * clip01(good_count / lock_count)`, where `clip01` limits its argument to `[0, 1]`.
- Use event-body state updates plus local analog helper functions rather than user task/endtask syntax.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A only. Do not use user `task`/`endtask`, Verilog-AMS digital kernels, branch current contributions, transistor devices, `ddt()`, or `idt()`. Do not hard-code testbench-specific stimulus timing.

## Output Contract

Return only `event_reacquire_lock_detector.va` implementing the public module. The file must compile under Spectre-compatible Verilog-A and must not require additional modules, include files beyond standard disciplines, or testbench changes.
