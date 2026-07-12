# Crossing Metric Writer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Crossing Metric Writer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `file_metric_writer.va`:
  - Module `file_metric_writer` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `done` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `file_metric_writer` as `XDUT` with ordered public binding: vin=vin, done=done.

## Public Parameter Contract

- `file_metric_writer.filename` defaults to `metric.out`; valid range: non-empty relative basename without directory separators; runner supplies the writable working directory; selects the basename of the single metric text file opened at startup and receiving the first-crossing time.
- `file_metric_writer.vth` defaults to `0.45` V; valid range: any finite voltage; sets the rising-crossing threshold for vin.
- `file_metric_writer.tr` defaults to `3e-10` s; valid range: tr > 0; sets done output rise and fall smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FILE_OPEN`: exercise and make observable: The filename parameter names exactly one metric file basename in the runner-provided writable working directory; absolute paths and directory traversal are outside the public contract. Required traces: `time`, `vin`, `done`.
- `P_FIRST_RISING_CROSSING`: exercise and make observable: The first rising crossing of vin through vth is the event that records the metric and latches completion. Required traces: `time`, `vin`, `done`.
- `P_RECORDED_TIME`: exercise and make observable: The metric file contains exactly one text record of the form `cross <time_seconds>` followed by a newline, where <time_seconds> is the first rising crossing time. Required traces: `time`, `vin`, `done`.
- `P_DONE_LATCH`: exercise and make observable: done remains low before the first qualifying crossing and high after it, with transition smoothing set by tr. Required traces: `time`, `vin`, `done`.
- `P_SINGLE_RECORD`: exercise and make observable: Later vin crossings do not clear done or create additional metric records. Required traces: `time`, `vin`, `done`.

The required trace names are: `time`, `vin`, `done`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
