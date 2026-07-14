# PLL Timing Monitor System Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PLL Timing Monitor System` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pll_timing_monitor_top.va`:
  - Module `pll_timing_monitor_top` (entry)
    - position 0: `ref_clk` (input, electrical)
    - position 1: `fb_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `up` (output, electrical)
    - position 5: `down` (output, electrical)
    - position 6: `lock` (output, electrical)
    - position 7: `reacquire` (output, electrical)
    - position 8: `div2_clk` (output, electrical)
    - position 9: `phase_3` (output, electrical)
    - position 10: `phase_2` (output, electrical)
    - position 11: `phase_1` (output, electrical)
    - position 12: `phase_0` (output, electrical)
- Artifact `phase_detector.va`:
  - Module `phase_detector` (required_submodule)
    - position 0: `ref_clk` (input, electrical)
    - position 1: `fb_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `up` (output, electrical)
    - position 5: `down` (output, electrical)
    - position 6: `phase_3` (output, electrical)
    - position 7: `phase_2` (output, electrical)
    - position 8: `phase_1` (output, electrical)
    - position 9: `phase_0` (output, electrical)
    - position 10: `compare_tick` (output, electrical)
    - position 11: `out_of_window` (output, electrical)
- Artifact `divider.va`:
  - Module `divider` (required_submodule)
    - position 0: `fb_clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `div2_clk` (output, electrical)
- Artifact `lock_detector.va`:
  - Module `lock_detector` (required_submodule)
    - position 0: `compare_tick` (input, electrical)
    - position 1: `out_of_window` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `lock` (output, electrical)
- Artifact `reacquire_timer.va`:
  - Module `reacquire_timer` (required_submodule)
    - position 0: `compare_tick` (input, electrical)
    - position 1: `out_of_window` (input, electrical)
    - position 2: `lock` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `reacquire` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pll_timing_monitor_top` as `XDUT` with ordered public binding: ref_clk=ref_clk, fb_clk=fb_clk, rst=rst, enable=enable, up=up, down=down, lock=lock, reacquire=reacquire, div2_clk=div2_clk, phase_3=phase_3, phase_2=phase_2, phase_1=phase_1, phase_0=phase_0.

## Public Parameter Contract

- `pll_timing_monitor_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module pll_timing_monitor_top.
- `pll_timing_monitor_top.vss` defaults to `0.0`; valid range: finite; overrides vss for module pll_timing_monitor_top.
- `pll_timing_monitor_top.vth` defaults to `0.45`; valid range: finite; overrides vth for module pll_timing_monitor_top.
- `pll_timing_monitor_top.lock_window` defaults to `2`; valid range: integer; overrides lock_window for module pll_timing_monitor_top.
- `pll_timing_monitor_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module pll_timing_monitor_top.
- `phase_detector.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module phase_detector.
- `phase_detector.vss` defaults to `0.0`; valid range: finite; overrides vss for module phase_detector.
- `phase_detector.vth` defaults to `0.45`; valid range: finite; overrides vth for module phase_detector.
- `phase_detector.lock_window` defaults to `2`; valid range: integer; overrides lock_window for module phase_detector.
- `phase_detector.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module phase_detector.
- `divider.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module divider.
- `divider.vss` defaults to `0.0`; valid range: finite; overrides vss for module divider.
- `divider.vth` defaults to `0.45`; valid range: finite; overrides vth for module divider.
- `divider.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module divider.
- `lock_detector.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module lock_detector.
- `lock_detector.vss` defaults to `0.0`; valid range: finite; overrides vss for module lock_detector.
- `lock_detector.vth` defaults to `0.45`; valid range: finite; overrides vth for module lock_detector.
- `lock_detector.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module lock_detector.
- `reacquire_timer.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module reacquire_timer.
- `reacquire_timer.vss` defaults to `0.0`; valid range: finite; overrides vss for module reacquire_timer.
- `reacquire_timer.vth` defaults to `0.45`; valid range: finite; overrides vth for module reacquire_timer.
- `reacquire_timer.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module reacquire_timer.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_DISABLE_CLEAR`: exercise and make observable: Reset or low enable clears pulse, lock, reacquire, divider, and phase-code outputs. Required traces: `time`, `rst`, `enable`, `up`, `down`, `lock`, `reacquire`, `div2_clk`, `phase_3`, `phase_2`, `phase_1`, `phase_0`.
- `P_PHASE_COMPARE`: exercise and make observable: UP and DOWN identify which observed rising edge led each completed comparison. Required traces: `time`, `ref_clk`, `fb_clk`, `rst`, `enable`, `up`, `down`.
- `P_PHASE_CODE`: exercise and make observable: The offset-binary phase code updates by one per completed comparison and clamps to its public range. Required traces: `time`, `ref_clk`, `fb_clk`, `rst`, `enable`, `phase_3`, `phase_2`, `phase_1`, `phase_0`.
- `P_DIVIDE_BY_FOUR_EDGES`: exercise and make observable: DIV2 toggles after each pair of feedback-clock rising edges. Required traces: `time`, `fb_clk`, `rst`, `enable`, `div2_clk`.
- `P_LOCK_REACQUIRE`: exercise and make observable: Lock requires four consecutive in-window comparisons and reacquire requires two post-lock out-of-window comparisons. Required traces: `time`, `ref_clk`, `fb_clk`, `rst`, `enable`, `lock`, `reacquire`, `phase_3`, `phase_2`, `phase_1`, `phase_0`.

The required trace names are: `time`, `ref_clk`, `fb_clk`, `rst`, `enable`, `up`, `down`, `lock`, `reacquire`, `div2_clk`, `phase_3`, `phase_2`, `phase_1`, `phase_0`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
