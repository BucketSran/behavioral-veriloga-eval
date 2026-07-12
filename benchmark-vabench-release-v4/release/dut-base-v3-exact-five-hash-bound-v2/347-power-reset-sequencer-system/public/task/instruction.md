# Power and Reset Sequencer

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `power_reset_seq_top.va`, `por_detector.va`, `reset_synchronizer.va`, `enable_sequencer.va`, `ready_flag.va`
- Public top module: `power_reset_seq_top`
- Required public modules: `power_reset_seq_top`, `por_detector`, `reset_synchronizer`, `enable_sequencer`, `ready_flag`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `power_reset_seq_top` with positional electrical ports `vdd_sense, clk, rst_n_ext, enable_req, por_n, rst_n_core, en_ana, en_dig, ready`. All top-level ports are electrical.

Each required public module has a fixed ordered electrical interface and parameter contract; these are part of the submitted artifact contract:

- `por_detector(vdd_sense, clk, rst_n_ext, por_n)`; parameters: vhi=0.9, vlo=0.0, vpor=0.72, vth=0.45, tr=200e-12.
- `reset_synchronizer(clk, por_n, enable_req, rst_n_core)`; parameters: vhi=0.9, vlo=0.0, vth=0.45, tr=200e-12.
- `enable_sequencer(clk, rst_n_core, en_ana, en_dig)`; parameters: vhi=0.9, vlo=0.0, vth=0.45, tr=200e-12.
- `ready_flag(clk, en_ana, en_dig, ready)`; parameters: vhi=0.9, vlo=0.0, vth=0.45, tr=200e-12.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vhi = 0.9 V`: logic high output level.
- `vlo = 0.0 V`: logic low output level.
- `vpor = 0.72 V`: power-good threshold for `vdd_sense`.
- `vth = 0.45 V`: threshold for digital control inputs.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- `por_detector` drives `por_n` high only after `vdd_sense` has been above `vpor` for two consecutive rising `clk` edges while `rst_n_ext` is high.
- When power is not good or external reset is low, drive all outputs low and restart the sequence.
- After `por_n` is high and `enable_req` is high, `reset_synchronizer` releases `rst_n_core` on the next rising `clk` edge.
- `enable_sequencer` then asserts `en_ana` one clock after core reset release and `en_dig` one clock after `en_ana`.
- `ready_flag` asserts `ready` one clock after both enables are high.
- If `vdd_sense` drops below `vpor` or `rst_n_ext` goes low, all outputs must return low without waiting for the sequence to finish.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `power_reset_seq_top.va`
- `por_detector.va`
- `reset_synchronizer.va`
- `enable_sequencer.va`
- `ready_flag.va`
