# PFD Timer Reset Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pfd_timer_reset.va`:
  - Module `pfd_timer_reset` (entry)
    - position 0: `a` (input, electrical)
    - position 1: `b` (input, electrical)
    - position 2: `ub` (output, electrical)
    - position 3: `d` (output, electrical)

## Public Parameter Contract

- `pfd_timer_reset.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pfd_timer_reset.vh` defaults to `0.9`; valid range: finite; overrides vh.
- `pfd_timer_reset.reset_delay` defaults to `100p from [0:inf)`; valid range: finite; overrides reset_delay.
- `pfd_timer_reset.tr` defaults to `10p from [0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PFD_STATE_AND_POLARITY`: restore: A rising crossing of `a` asserts the UP state and a rising crossing of `b` asserts the DOWN state; drive `ub` active-low for UP and `d` active-high for DOWN. Required traces: `time`, `a`, `b`, `d`, `ub`.
- `P_DELAYED_MUTUAL_RESET`: restore: After both detector states have occurred, schedule the mutual reset after `reset_delay` instead of clearing immediately or never clearing. Required traces: `time`, `a`, `b`, `d`, `ub`.
- `P_OUTPUT_LEVELS_AND_TRANSITIONS`: restore: Drive asserted/deasserted outputs near the public `vh`/`0 V` levels with the declared transition smoothing. Required traces: `time`, `a`, `b`, `d`, `ub`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pfd_timer_reset.va`.
Every supplied `.va` file is editable; do not add or omit files.
