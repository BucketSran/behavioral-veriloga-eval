# PFD With External Active Low Reset
## Task Contract
Implement `pfd_active_low_reset.va`, a L1 voltage-domain clock timing DUT for PFD With External Active Low Reset.
## Public Verilog-A Interface
Declare `module pfd_active_low_reset(ref, fb, rstb, up, down);` with scalar electrical ports. Port order is normative: `ref` (input), `fb` (input), `rstb` (input), `up` (output), `down` (output).
## Public Parameter Contract
- `vth = 0.45`: overrides vth.
- `vh = 0.9`: overrides vh.
- `reset_delay = 80p from [0:inf)`: overrides reset_delay.
- `tr = 10p from [0:inf)`: overrides tr.

## Required Behavior
- `P_WHEN_RSTB_IS_BELOW_VTH_CLEAR`: When `rstb` is below `vth`, clear both PFD states and hold both outputs low. While `rstb` is high, a rising crossing of `ref` asserts `up`, and a rising crossing of `fb` asserts `down`. Once both states have occurred, schedule a reset after `reset_delay` and clear both states at that timer event. The reset input must also clear a pending one-sided UP or DOWN state even if the opposite edge has not arrived.
- `P_VTH_0_45_V_THRESHOLD_FOR`: `vth = 0.45 V`: threshold for `ref`, `fb`, and `rstb`.
- `P_VH_0_9_V_LOGIC_HIGH`: `vh = 0.9 V`: logic-high output level.
- `P_RESET_DELAY_80_PS_FROM_0`: `reset_delay = 80 ps from [0:inf)`: delay from the moment both detector states are asserted to the mutual reset event.
- `P_TR_10_PS_FROM_0_INF`: `tr = 10 ps from [0:inf)`: output transition smoothing time.
- `P_VTH_0_45_V_THRESHOLD_FOR_2`: - `vth = 0.45 V`: threshold for `ref`, `fb`, and `rstb`. - `vh = 0.9 V`: logic-high output level. - `reset_delay = 80 ps from [0:inf)`: delay from the moment both detector states are asserted to the mutual reset event. - `tr = 10 ps from [0:inf)`: output transition smoothing time.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `pfd_active_low_reset.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
