# Auto-zero Comparator Preamplifier

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `autozero_comparator_preamplifier_top.va`, `offset_store_cell.va`, `clocked_comparator_core.va`
- Public top module: `autozero_comparator_preamplifier_top`
- Required public modules: `autozero_comparator_preamplifier_top`, `offset_store_cell`, `clocked_comparator_core`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `autozero_comparator_preamplifier_top` with positional electrical ports `vinp, vinn, clk, rst, az_en, eval_en, decision, offset_store, ready`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear stored offset, `decision`, and `ready`.
- During an auto-zero clock update with `az_en` high, store the apparent differential offset between `vinp` and `vinn`.
- During an evaluation clock update with `eval_en` high, subtract the stored offset from the live differential input.
- Drive `decision` high for corrected nonnegative differential input and low otherwise.
- Expose stored offset on `offset_store` and assert `ready` after at least one auto-zero update.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `autozero_comparator_preamplifier_top.va`
- `offset_store_cell.va`
- `clocked_comparator_core.va`
