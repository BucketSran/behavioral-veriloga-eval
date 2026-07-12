# Bang-bang CDR Loop

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `cdr_top.va`, `bbpd.va`, `loop_filter_code.va`, `phase_rotator.va`
- Public top module: `cdr_top`
- Required public modules: `cdr_top`, `bbpd`, `loop_filter_code`, `phase_rotator`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `cdr_top` with positional electrical ports `data_edge, ref_clk, rst, enable, recovered_clk, early, late, phase_4, phase_3, phase_2, phase_1, phase_0, lock`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock, edge, reset, and enable inputs.
- `phase_center = 16`: reset phase code.
- `unit_phase_delay = 5e-12 s`: recovered-clock delay represented by one phase-code step.
- `lock_window = 2`: maximum edge-code error counted as locked.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, reset the phase code to `phase_center`, clear `early`, `late`, and `lock`.
- `bbpd` compares each rising `data_edge` event with the nearest rising `recovered_clk` event. Report `early` when the recovered-clock edge occurs before the data edge and `late` when it occurs after the data edge; coincident edges clear both decisions.
- `loop_filter_code` increments the phase code on late decisions and decrements it on early decisions, clamped to 0 through 31.
- `phase_rotator` must generate `recovered_clk` by delaying both edges of `ref_clk` by `phase_code * unit_phase_delay`. Latch the code separately for each originating edge so a later code update does not retime an already pending output edge.
- Drive `phase_4..phase_0` as voltage-coded copies of the current phase code.
- Assert `lock` after four consecutive decisions whose absolute phase-code error is within `lock_window`.
- If two consecutive out-of-window decisions occur after lock, deassert `lock` and continue correcting. Reset or low `enable` cancels pending delayed edges, clears comparison history, and drives `recovered_clk` low.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `cdr_top.va`
- `bbpd.va`
- `loop_filter_code.va`
- `phase_rotator.va`
