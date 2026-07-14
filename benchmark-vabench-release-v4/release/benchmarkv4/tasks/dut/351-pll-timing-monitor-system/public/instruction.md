# PLL Timing Monitor System

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `pll_timing_monitor_top.va`, `phase_detector.va`, `divider.va`, `lock_detector.va`, `reacquire_timer.va`
- Public top module: `pll_timing_monitor_top`
- Required public modules: `pll_timing_monitor_top`, `phase_detector`, `divider`, `lock_detector`, `reacquire_timer`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `pll_timing_monitor_top` with positional electrical ports `ref_clk, fb_clk, rst, enable, up, down, lock, reacquire, div2_clk, phase_3, phase_2, phase_1, phase_0`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `lock_window = 2`: maximum absolute phase-code error counted as locked.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, clear `up`, `down`, `lock`, `reacquire`, `div2_clk`, and the phase code.
- `divider` must toggle `div2_clk` on every second rising edge of `fb_clk`.
- `phase_detector` compares rising `ref_clk` and `fb_clk` events: assert `up` when the reference edge leads, assert `down` when the feedback edge leads, and clear both after the opposite edge arrives.
- Treat the arrival of one rising edge from each clock as one completed comparison cycle. Increment the signed phase estimate by exactly one when the reference edge arrived first, decrement it by exactly one when the feedback edge arrived first, and leave it unchanged for coincident edges. Clamp the estimate to -8 through +7.
- Represent the signed phase estimate on `phase_3..phase_0` as offset binary with code 8 representing zero phase error.
- `lock_detector` asserts `lock` after four consecutive comparison cycles with absolute phase-code error less than or equal to `lock_window`.
- `reacquire_timer` asserts `reacquire` when the system was locked and then observes two consecutive out-of-window phase comparisons. A reset or low `enable` clears any unmatched edge and all consecutive-cycle history.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `pll_timing_monitor_top.va`
- `phase_detector.va`
- `divider.va`
- `lock_detector.va`
- `reacquire_timer.va`
