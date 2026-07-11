# PFD Timer Reset

## Task Contract
Implement `pfd_timer_reset.va`, a single voltage-domain phase-frequency detector DUT with delayed mutual reset. This is an L1 clock/timing component; it is functionally close to `300-pfd-active-low-reset`, so counting both rows separately requires an explicit duplicate policy.

## Public Verilog-A Interface
Declare module `pfd_timer_reset(a, b, ub, d)` with scalar electrical ports. Inputs `a` and `b` are voltage-coded edge inputs. Output `ub` is the active-low UP output, and `d` is the active-high DOWN output.

## Public Parameter Contract
Provide overrideable public parameters:

- `vth = 0.45 V`: rising-edge threshold for `a` and `b`.
- `vh = 0.9 V`: logic-high output level.
- `reset_delay = 100 ps from [0:inf)`: delay from the moment both detector states are asserted to the mutual reset event.
- `tr = 10 ps from [0:inf)`: output transition smoothing time.

## Required Behavior
A rising crossing of `a` asserts the UP state. A rising crossing of `b` asserts the DOWN state. Drive `ub` near `0 V` while UP is asserted and near `vh` otherwise. Drive `d` near `vh` while DOWN is asserted and near `0 V` otherwise. Once both states have occurred, schedule a reset after `reset_delay` and clear both states at that timer event.

## Modeling Constraints
Use voltage contributions and smooth output transitions. Do not emit or modify support testbenches, add checker logic, hard-code testbench waveform sample points, add simulator side channels, use current contributions, transistor-level devices, `ddt()`, or `idt()`.

## Output Contract
Return exactly one source artifact named `pfd_timer_reset.va`.
