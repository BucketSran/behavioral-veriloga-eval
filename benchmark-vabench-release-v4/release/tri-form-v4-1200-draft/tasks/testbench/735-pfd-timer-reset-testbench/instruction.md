# PFD Timer Reset Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PFD Timer Reset` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pfd_timer_reset.va`:
  - Module `pfd_timer_reset` (entry)
    - position 0: `a` (input, electrical)
    - position 1: `b` (input, electrical)
    - position 2: `ub` (output, electrical)
    - position 3: `d` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pfd_timer_reset` as `XDUT` with ordered public binding: a=a, b=b, ub=ub, d=d.

## Public Parameter Contract

- `pfd_timer_reset.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pfd_timer_reset.vh` defaults to `0.9`; valid range: finite; overrides vh.
- `pfd_timer_reset.reset_delay` defaults to `100p from [0:inf)`; valid range: finite; overrides reset_delay.
- `pfd_timer_reset.tr` defaults to `10p from [0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_PFD_STATE_AND_POLARITY`: exercise and make observable: A rising crossing of `a` asserts the UP state and a rising crossing of `b` asserts the DOWN state; drive `ub` active-low for UP and `d` active-high for DOWN. Required traces: `time`, `a`, `b`, `d`, `ub`.
- `P_DELAYED_MUTUAL_RESET`: exercise and make observable: After both detector states have occurred, schedule the mutual reset after `reset_delay` instead of clearing immediately or never clearing. Required traces: `time`, `a`, `b`, `d`, `ub`.
- `P_OUTPUT_LEVELS_AND_TRANSITIONS`: exercise and make observable: Drive asserted/deasserted outputs near the public `vh`/`0 V` levels with the declared transition smoothing. Required traces: `time`, `a`, `b`, `d`, `ub`.

The required trace names are: `time`, `a`, `b`, `d`, `ub`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
