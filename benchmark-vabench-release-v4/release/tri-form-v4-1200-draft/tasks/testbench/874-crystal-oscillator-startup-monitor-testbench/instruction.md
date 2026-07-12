# Crystal Oscillator Startup Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Crystal Oscillator Startup Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `crystal_oscillator_startup_monitor.va`:
  - Module `crystal_oscillator_startup_monitor` (entry)
    - position 0: `enable` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `clk_ref` (inout, electrical)
    - position 3: `osc_out` (inout, electrical)
    - position 4: `amp_metric` (inout, electrical)
    - position 5: `valid` (inout, electrical)
    - position 6: `startup_done` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `crystal_oscillator_startup_monitor` as `XDUT` with ordered public binding: enable=enable, rst=rst, clk_ref=clk_ref, osc_out=osc_out, amp_metric=amp_metric, valid=valid, startup_done=startup_done.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_ENABLE_IS`: exercise and make observable: On reset or when `enable` is low, clear oscillator amplitude, `osc_out`, `valid`, and `startup_done`. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_INCREASE_A_BEHAVIORAL_AMPLITUDE_STATE_BY`: exercise and make observable: Increase a behavioral amplitude state by `amp_step` on each rising `clk_ref` edge while enabled until `amp_target` is reached. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_CLAMP_THE_AMPLITUDE_AT_AMP_TARGET`: exercise and make observable: Clamp the amplitude at `amp_target` and expose it on `amp_metric`. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_TOGGLE_OSC_OUT_FROM_CLK_REF`: exercise and make observable: Toggle `osc_out` from `clk_ref` only after the amplitude state is nonzero. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_ASSERT_STARTUP_DONE_WHEN_AMP_METRIC`: exercise and make observable: Assert `startup_done` when `amp_metric` reaches `amp_target`. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.
- `P_ASSERT_VALID_AFTER_TWO_CONSECUTIVE_SLICED`: exercise and make observable: Assert `valid` after two consecutive sliced oscillator periods after startup is done. Required traces: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.

The required trace names are: `time`, `enable`, `rst`, `clk_ref`, `osc_out`, `amp_metric`, `valid`, `startup_done`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
