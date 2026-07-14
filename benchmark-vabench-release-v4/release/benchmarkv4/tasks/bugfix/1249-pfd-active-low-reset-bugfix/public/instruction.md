# PFD With External Active Low Reset Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pfd_active_low_reset.va`:
  - Module `pfd_active_low_reset` (entry)
    - position 0: `ref` (input, electrical)
    - position 1: `fb` (input, electrical)
    - position 2: `rstb` (input, electrical)
    - position 3: `up` (output, electrical)
    - position 4: `down` (output, electrical)

## Public Parameter Contract

- `pfd_active_low_reset.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pfd_active_low_reset.vh` defaults to `0.9`; valid range: finite; overrides vh.
- `pfd_active_low_reset.reset_delay` defaults to `80p from [0:inf)`; valid range: finite; overrides reset_delay.
- `pfd_active_low_reset.tr` defaults to `10p from [0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_WHEN_RSTB_IS_BELOW_VTH_CLEAR`: restore: When `rstb` is below `vth`, clear both PFD states and hold both outputs low. While `rstb` is high, a rising crossing of `ref` asserts `up`, and a rising crossing of `fb` asserts `down`. Once both states have occurred, schedule a reset after `reset_delay` and clear both states at that timer event. The reset input must also clear a pending one-sided UP or DOWN state even if the opposite edge has not arrived. Required traces: `time`, `down`, `fb`, `ref`, `rstb`, `up`.
- `P_VTH_0_45_V_THRESHOLD_FOR`: restore: `vth = 0.45 V`: threshold for `ref`, `fb`, and `rstb`. Required traces: `time`, `down`, `fb`, `ref`, `rstb`, `up`.
- `P_VH_0_9_V_LOGIC_HIGH`: restore: `vh = 0.9 V`: logic-high output level. Required traces: `time`, `down`, `fb`, `ref`, `rstb`, `up`.
- `P_RESET_DELAY_80_PS_FROM_0`: restore: `reset_delay = 80 ps from [0:inf)`: delay from the moment both detector states are asserted to the mutual reset event. Required traces: `time`, `down`, `fb`, `ref`, `rstb`, `up`.
- `P_TR_10_PS_FROM_0_INF`: restore: `tr = 10 ps from [0:inf)`: output transition smoothing time. Required traces: `time`, `down`, `fb`, `ref`, `rstb`, `up`.
- `P_VTH_0_45_V_THRESHOLD_FOR_2`: restore: - `vth = 0.45 V`: threshold for `ref`, `fb`, and `rstb`. - `vh = 0.9 V`: logic-high output level. - `reset_delay = 80 ps from [0:inf)`: delay from the moment both detector states are asserted to the mutual reset event. - `tr = 10 ps from [0:inf)`: output transition smoothing time. Required traces: `time`, `down`, `fb`, `ref`, `rstb`, `up`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pfd_active_low_reset.va`.
Every supplied `.va` file is editable; do not add or omit files.
