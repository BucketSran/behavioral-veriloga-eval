# Gain Estimator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Gain Estimator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `gain_estimator.va`:
  - Module `gain_estimator` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `vinp` (input, electrical)
    - position 3: `vinn` (input, electrical)
    - position 4: `voutp` (input, electrical)
    - position 5: `voutn` (input, electrical)
    - position 6: `gain_out` (output, electrical)
    - position 7: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `gain_estimator` as `XDUT` with ordered public binding: VDD=vdd, VSS=vss, vinp=vinp, vinn=vinn, voutp=voutp, voutn=voutn, gain_out=gain_out, valid=valid.

## Public Parameter Contract

- `gain_estimator.sample_period` defaults to `1e-09` s; valid range: sample_period > 0; sets periodic extrema-sampling interval.
- `gain_estimator.start_time` defaults to `2e-08` s; valid range: start_time >= 0; sets when samples begin contributing to extrema.
- `gain_estimator.gain_scale` defaults to `10.0` V/V represented at full scale; valid range: gain_scale > 0; sets gain represented by full-scale gain_out.
- `gain_estimator.min_input_span` defaults to `0.02` V; valid range: min_input_span > 0; sets minimum input span required to assert valid.
- `gain_estimator.tedge` defaults to `2e-10` s; valid range: tedge > 0; sets gain_out and valid transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_START_TIME_GATING`: exercise and make observable: Samples before start_time do not contribute to measured input or output extrema and valid remains low. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`, `valid`.
- `P_PERIODIC_EXTREMA`: exercise and make observable: At each sample_period after start_time, the estimator updates minima and maxima of the input and output differential voltages. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`, `gain_out`, `valid`.
- `P_VALIDITY_THRESHOLD`: exercise and make observable: Valid remains rail-low until the observed input differential span exceeds min_input_span and remains rail-high afterwards. Required traces: `time`, `vdd`, `vss`, `vinp`, `vinn`, `valid`.
- `P_SPAN_RATIO`: exercise and make observable: Once valid, the measured gain equals output differential span divided by input differential span. Required traces: `time`, `vinp`, `vinn`, `voutp`, `voutn`, `gain_out`, `valid`.
- `P_NORMALIZED_GAIN_OUTPUT`: exercise and make observable: Gain_out equals the VDD-to-VSS rail span multiplied by measured gain divided by gain_scale. Required traces: `time`, `vdd`, `vss`, `gain_out`, `valid`.
- `P_EVENT_UPDATED_TARGETS`: exercise and make observable: Gain_out and valid reflect event-updated retained targets with finite smoothing rather than continuously varying transition inputs. Required traces: `time`, `gain_out`, `valid`.

The required trace names are: `time`, `vdd`, `vss`, `vinp`, `vinn`, `voutp`, `voutn`, `gain_out`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
