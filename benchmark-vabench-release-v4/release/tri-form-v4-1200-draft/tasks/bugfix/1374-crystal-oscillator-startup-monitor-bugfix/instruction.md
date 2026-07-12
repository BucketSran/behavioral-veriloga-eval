# Crystal Oscillator Startup Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `crystal_oscillator_startup_monitor.va`:
  - Module `crystal_oscillator_startup_monitor` (entry)
    - position 0: `enable` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `clk_ref` (inout, electrical)
    - position 3: `osc_out` (inout, electrical)
    - position 4: `amp_metric` (inout, electrical)
    - position 5: `valid` (inout, electrical)
    - position 6: `startup_done` (inout, electrical)

## Public Parameter Contract

- `crystal_oscillator_startup_monitor.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `crystal_oscillator_startup_monitor.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `crystal_oscillator_startup_monitor.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `crystal_oscillator_startup_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `crystal_oscillator_startup_monitor.amp_step` defaults to `40e-3`; valid range: finite; overrides amp_step.
- `crystal_oscillator_startup_monitor.amp_target` defaults to `0.3`; valid range: finite; overrides amp_target.
- `crystal_oscillator_startup_monitor.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `crystal_oscillator_startup_monitor.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_ENABLE_IS`: restore: On reset or when `enable` is low, clear oscillator amplitude, `osc_out`, `valid`, and `startup_done`. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_INCREASE_A_BEHAVIORAL_AMPLITUDE_STATE_BY`: restore: Increase a behavioral amplitude state by `amp_step` on each rising `clk_ref` edge while enabled until `amp_target` is reached. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_CLAMP_THE_AMPLITUDE_AT_AMP_TARGET`: restore: Clamp the amplitude at `amp_target` and expose it on `amp_metric`. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_TOGGLE_OSC_OUT_FROM_CLK_REF`: restore: Toggle `osc_out` from `clk_ref` only after the amplitude state is nonzero. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_ASSERT_STARTUP_DONE_WHEN_AMP_METRIC`: restore: Assert `startup_done` when `amp_metric` reaches `amp_target`. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_ASSERT_VALID_AFTER_TWO_CONSECUTIVE_SLICED`: restore: Assert `valid` after two consecutive sliced oscillator periods after startup is done. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `crystal_oscillator_startup_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
