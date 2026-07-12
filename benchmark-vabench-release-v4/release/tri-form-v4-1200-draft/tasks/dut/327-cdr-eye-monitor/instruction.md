# CDR Eye Monitor

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `cdr_eye_monitor_top.va`, `edge_margin_sampler.va`, `eye_metric_filter.va`
- Public top module: `cdr_eye_monitor_top`
- Required public modules: `cdr_eye_monitor_top`, `edge_margin_sampler`, `eye_metric_filter`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `cdr_eye_monitor_top` with positional electrical ports `data_in, sample_clk, rst, enable, early, late, eye_metric, lock_hint, valid`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `eye_min = 0.55 V`: lock-hint threshold.
- `edge_window = 600 ps`: timing window used to classify nearby data edges around a sampling edge.

## Required Behavior

- On reset or when disabled, clear early/late flags, eye metric, lock hint, and `valid`.
- On each rising sampling-clock edge, produce a valid timing observation.
- Raise `early` for a data transition within `edge_window` before a sampling edge, and raise `late` for a transition within `edge_window` after it. Keep the flags mutually exclusive.
- Drive `eye_metric` from the measured sample margin; samples without a nearby transition represent an open-eye observation.
- Assert `lock_hint` after four consecutive samples with eye metric above `eye_min`.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `cdr_eye_monitor_top.va`
- `edge_margin_sampler.va`
- `eye_metric_filter.va`
