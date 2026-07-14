# Reference Step Clock Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ref_step_clk.va`:
  - Module `ref_step_clk` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `CLK` (output, electrical)

## Public Parameter Contract

- `ref_step_clk.period_pre` defaults to `2e-08` s; valid range: period_pre > 0; sets the full clock period before t_switch.
- `ref_step_clk.period_post` defaults to `1.95e-08` s; valid range: period_post > 0; sets the full clock period for cycles scheduled after t_switch.
- `ref_step_clk.t_switch` defaults to `2e-06` s; valid range: t_switch >= 0; sets the cadence-change boundary.
- `ref_step_clk.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets CLK rise and fall smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SUPPLY_REFERENCED_RAILS`: restore: CLK low and high levels track VSS and VDD respectively. Required traces: `time`, `VDD`, `VSS`, `CLK`.
- `P_PRE_SWITCH_PERIOD`: restore: Clock cycles before t_switch have full period period_pre. Required traces: `time`, `CLK`.
- `P_POST_SWITCH_PERIOD`: restore: Clock cycles scheduled after t_switch have full period period_post. Required traces: `time`, `CLK`.
- `P_CADENCE_STEP`: restore: The waveform changes cadence near t_switch without stopping, duplicating, or losing clock transitions. Required traces: `time`, `CLK`.
- `P_HALF_DUTY_CYCLE`: restore: CLK duty cycle remains close to 50 percent on both sides of the cadence step. Required traces: `time`, `CLK`.
- `P_PARAMETERIZED_TIMING`: restore: Nearby legal overrides of period_pre, period_post, t_switch, and tedge produce the corresponding periods, switch boundary, and edge smoothing. Required traces: `time`, `VDD`, `VSS`, `CLK`.

## Modeling Constraints

- Generate a deterministic supply-referenced square wave with a parameterized frequency step.
- Use event-driven state and smoothed voltage contributions only.
- Do not hard-code validation stop times or sample windows, and do not use current contributions, transistor-level devices, validation hooks, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ref_step_clk.va`.
Every supplied `.va` file is editable; do not add or omit files.
