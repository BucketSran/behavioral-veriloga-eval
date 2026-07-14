# CDR Eye Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cdr_eye_monitor_top.va`:
  - Module `cdr_eye_monitor_top` (entry)
    - position 0: `data_in` (input, electrical)
    - position 1: `sample_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `early` (output, electrical)
    - position 5: `late` (output, electrical)
    - position 6: `eye_metric` (output, electrical)
    - position 7: `lock_hint` (output, electrical)
    - position 8: `valid` (output, electrical)
- Artifact `edge_margin_sampler.va`:
  - Module `edge_margin_sampler` (required_submodule)
    - position 0: `data_in` (input, electrical)
    - position 1: `sample_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `early` (output, electrical)
    - position 5: `late` (output, electrical)
    - position 6: `margin` (output, electrical)
    - position 7: `valid` (output, electrical)
- Artifact `eye_metric_filter.va`:
  - Module `eye_metric_filter` (required_submodule)
    - position 0: `sample_clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `margin` (input, electrical)
    - position 4: `sample_valid` (input, electrical)
    - position 5: `eye_metric` (output, electrical)
    - position 6: `lock_hint` (output, electrical)

## Public Parameter Contract

- `cdr_eye_monitor_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `cdr_eye_monitor_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `cdr_eye_monitor_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `cdr_eye_monitor_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `cdr_eye_monitor_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `cdr_eye_monitor_top.eye_min` defaults to `0.55`; valid range: finite; overrides eye_min.
- `cdr_eye_monitor_top.edge_window` defaults to `600p from (0:inf)`; valid range: finite; overrides edge_window.
- `edge_margin_sampler.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `edge_margin_sampler.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `edge_margin_sampler.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `edge_margin_sampler.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `edge_margin_sampler.edge_window` defaults to `600p from (0:inf)`; valid range: finite; overrides edge_window.
- `eye_metric_filter.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `eye_metric_filter.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `eye_metric_filter.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `eye_metric_filter.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `eye_metric_filter.eye_min` defaults to `0.55`; valid range: finite; overrides eye_min.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear early/late flags, eye metric, lock hint, and `valid`. Required traces: `time`, `data_in`, `sample_clk`, `rst`, `enable`, `early`, `late`, `eye_metric`, `lock_hint`, `valid`.
- `P_ON_EACH_SAMPLING_CLOCK_EDGE_COMPARE`: restore: On each sampling-clock edge, compare the sampled data level with the previous sample. Required traces: `time`, `data_in`, `sample_clk`, `rst`, `enable`, `early`, `late`, `eye_metric`, `lock_hint`, `valid`.
- `P_RAISE_EARLY_OR_LATE_ACCORDING_TO`: restore: Raise `early` or `late` according to the sign of the edge-position proxy around the sample instant. Required traces: `time`, `data_in`, `sample_clk`, `rst`, `enable`, `early`, `late`, `eye_metric`, `lock_hint`, `valid`.
- `P_DRIVE_EYE_METRIC_FROM_RECENT_TRANSITION`: restore: Drive `eye_metric` from recent transition stability and sample margin. Required traces: `time`, `data_in`, `sample_clk`, `rst`, `enable`, `early`, `late`, `eye_metric`, `lock_hint`, `valid`.
- `P_ASSERT_LOCK_HINT_AFTER_FOUR_CONSECUTIVE`: restore: Assert `lock_hint` after four consecutive samples with eye metric above `eye_min`. Required traces: `time`, `data_in`, `sample_clk`, `rst`, `enable`, `early`, `late`, `eye_metric`, `lock_hint`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cdr_eye_monitor_top.va`, `edge_margin_sampler.va`, `eye_metric_filter.va`.
Every supplied `.va` file is editable; do not add or omit files.
