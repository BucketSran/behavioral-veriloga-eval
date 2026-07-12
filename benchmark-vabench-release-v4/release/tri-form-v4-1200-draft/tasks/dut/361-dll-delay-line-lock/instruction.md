# DLL Delay-line Lock

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `dll_top.va`, `phase_detector.va`, `delay_line.va`, `lock_detector.va`
- Public top module: `dll_top`
- Required public modules: `dll_top`, `phase_detector`, `delay_line`, `lock_detector`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `dll_top` with positional electrical ports `ref_clk, in_clk, rst, enable, delayed_clk, up, down, delay_4, delay_3, delay_2, delay_1, delay_0, lock`. All top-level ports are electrical.

Each required public helper module must be declared with these positional electrical ports:

- `phase_detector(ref_clk, delayed_clk, rst, enable, up, down, decision_clk, edge_error)`
- `delay_line(in_clk, rst, enable, delay_4, delay_3, delay_2, delay_1, delay_0, delayed_clk)`
- `lock_detector(decision_clk, up, down, edge_error, rst, enable, delay_4, delay_3, delay_2, delay_1, delay_0, lock)`

The top module must expose exactly the public top-level port order above and connect the required helper modules as part of the DUT package.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clocks, reset, and enable.
- `delay_center = 16`: reset delay code.
- `unit_delay = 5e-12 s`: delay represented by one code step.
- `lock_window = 1`: maximum code error counted as locked.
- `tr = 100 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, reset the delay code to `delay_center`, clear `up`, `down`, and `lock`.
- `delay_line` generates `delayed_clk` by delaying `in_clk` edges according to the current delay code.
- `phase_detector` treats one rising edge from each clock as a completed comparison cycle. Request `up` and increment the delay code by one when `delayed_clk` arrived before `ref_clk`; request `down` and decrement the code by one when `delayed_clk` arrived after `ref_clk`; coincident edges request neither correction.
- Update the delay code once per completed comparison cycle, clamped to 0 through 31.
- Drive `delay_4..delay_0` as voltage-coded copies of the current delay code.
- `lock_detector` asserts `lock` after four consecutive comparisons whose absolute edge-time error is no greater than `lock_window * unit_delay`.
- Unlike a PLL, this DUT must not synthesize a free-running oscillator; output edges derive from `in_clk` only.
- Latch the delay code independently for each originating input edge. A later correction must not retime an already pending edge. Reset or low `enable` cancels pending delayed edges, clears unmatched comparison edges, and drives `delayed_clk` low.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `dll_top.va`
- `phase_detector.va`
- `delay_line.va`
- `lock_detector.va`
