# Multi-channel Sample/Mux/Readout

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `sample_mux_readout_top.va`, `sample_hold_bank.va`, `mux_controller.va`, `output_driver.va`
- Public top module: `sample_mux_readout_top`
- Required public modules: `sample_mux_readout_top`, `sample_hold_bank`, `mux_controller`, `output_driver`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `sample_mux_readout_top` with positional electrical ports `ch0, ch1, ch2, ch3, clk, rst, sample, read, out, ch_sel_1, ch_sel_0, valid`. All top-level ports are electrical.

Each required public module has a fixed ordered electrical interface and parameter contract; these are part of the submitted artifact contract:

- `sample_hold_bank(ch0, ch1, ch2, ch3, clk, rst, sample, hold0, hold1, hold2, hold3)`; parameters: vth=0.45, tr=200e-12.
- `mux_controller(clk, rst, read, ch_sel_1, ch_sel_0, valid)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200e-12.
- `output_driver(hold0, hold1, hold2, hold3, clk, rst, read, ch_sel_1, ch_sel_0, out)`; parameters: vth=0.45, tr=200e-12.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for `clk`, `rst`, `sample`, and `read`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the held channel values, read pointer, `out`, `ch_sel_1`, `ch_sel_0`, and `valid`.
- When `sample` is high on a rising `clk` edge, `sample_hold_bank` captures `ch0..ch3` simultaneously.
- When `read` is high on a rising `clk` edge, `mux_controller` outputs the next held channel in order 0, 1, 2, 3 and then wraps to 0.
- `output_driver` drives `out` to the selected held channel voltage and asserts `valid` on read cycles.
- `ch_sel_1..ch_sel_0` must expose the channel index currently driven on `out`.
- When `read` is low, hold `out` and deassert `valid` without advancing the pointer.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `sample_mux_readout_top.va`
- `sample_hold_bank.va`
- `mux_controller.va`
- `output_driver.va`
