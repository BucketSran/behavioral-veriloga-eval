# Sampled Error Update Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Sampled Error Update Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sampled_error_update_monitor.va`:
  - Module `sampled_error_update_monitor` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `sample` (input, electrical)
    - position 3: `target` (input, electrical)
    - position 4: `coef` (input, electrical)
    - position 5: `out` (output, electrical)
    - position 6: `err_metric` (output, electrical)
    - position 7: `progress` (output, electrical)

Stable public Spectre binding:

The submitted `testbench.scs` must use the supplied DUT through this public binding:

- Include path: `./dut/sampled_error_update_monitor.va`
- DUT instance: `XDUT (clk rst sample target coef out err_metric progress) sampled_error_update_monitor`
- Required saved public traces: `clk`, `coef`, `err_metric`, `out`, `progress`, `rst`, `sample`, `target`
- Use one bounded transient analysis with a finite positive stop time.

You must design the stimulus yourself. Save traces as bare public signal names
(for example `clk`, not suffixed or hierarchical forms such as `clk:V` or
`XDUT.clk`). Do not redefine the DUT, drive DUT output nets, save
hierarchical/private nodes, or use checker/gold/internal files.

## Public Parameter Contract

- `sampled_error_update_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `sampled_error_update_monitor.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `sampled_error_update_monitor.err_fullscale` defaults to `0.50`; valid range: finite; overrides err_fullscale.
- `sampled_error_update_monitor.err_window` defaults to `0.040`; valid range: finite; overrides err_window.
- `sampled_error_update_monitor.ready_count` defaults to `3`; valid range: finite; overrides ready_count.
- `sampled_error_update_monitor.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_CLEARS_STATE_AND_OBSERVABLES`: exercise and make observable: While rst is high at a rising clock edge, clear the stable count, out, err_metric, and progress. Required traces: `clk`, `coef`, `err_metric`, `out`, `progress`, `rst`, `sample`, `target`, `time`.
- `P_CORRECTED_OUTPUT_USES_SAMPLE_TARGET_AND_COEF`: exercise and make observable: At each enabled positive clock edge, compute the clipped coefficient and drive the clamped corrected sample from sample, target, and coef. Required traces: `clk`, `coef`, `err_metric`, `out`, `progress`, `rst`, `sample`, `target`, `time`.
- `P_ERROR_METRIC_REPORTS_ABSOLUTE_ERROR`: exercise and make observable: Drive err_metric from the bounded absolute target-minus-sample error. Required traces: `clk`, `coef`, `err_metric`, `out`, `progress`, `rst`, `sample`, `target`, `time`.
- `P_PROGRESS_COUNTS_CONSECUTIVE_IN_WINDOW_SAMPLES`: exercise and make observable: Increment progress only for consecutive in-window sampled errors, clear it on an out-of-window sample, and saturate at ready_count. Required traces: `clk`, `coef`, `err_metric`, `out`, `progress`, `rst`, `sample`, `target`, `time`.


The following canonical public behavior is normative for this derived form:

- `P_RESET_CLEARS_STATE_AND_OBSERVABLES`: While rst is high at a rising clock edge, clear the stable count, out, err_metric, and progress.
- `P_CORRECTED_OUTPUT_USES_SAMPLE_TARGET_AND_COEF`: At each enabled positive clock edge, compute the clipped coefficient and drive the clamped corrected sample from sample, target, and coef.
- `P_ERROR_METRIC_REPORTS_ABSOLUTE_ERROR`: Drive err_metric from the bounded absolute target-minus-sample error.
- `P_PROGRESS_COUNTS_CONSECUTIVE_IN_WINDOW_SAMPLES`: Increment progress only for consecutive in-window sampled errors, clear it on an out-of-window sample, and saturate at ready_count.

The evaluator saves and may inspect these public trace signals: `time`, `clk`, `coef`, `err_metric`, `out`, `progress`, `rst`, `sample`, `target`.


The required trace names are: `time`, `clk`, `coef`, `err_metric`, `out`, `progress`, `rst`, `sample`, `target`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.

- V(target)-V(sample)

- V(sample)+coeff*error

- abs(error)/err_fullscale

- stable_count/ready_count
