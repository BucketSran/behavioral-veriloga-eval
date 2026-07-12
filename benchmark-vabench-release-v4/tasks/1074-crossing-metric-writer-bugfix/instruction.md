# Crossing Metric Writer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `file_metric_writer.va`:
  - Module `file_metric_writer` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `done` (output, electrical)

## Public Parameter Contract

- `file_metric_writer.filename` defaults to `metric.out`; valid range: non-empty relative basename without directory separators; runner supplies the writable working directory; selects the basename of the single metric text file opened at startup and receiving the first-crossing time.
- `file_metric_writer.vth` defaults to `0.45` V; valid range: any finite voltage; sets the rising-crossing threshold for vin.
- `file_metric_writer.tr` defaults to `3e-10` s; valid range: tr > 0; sets done output rise and fall smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FILE_OPEN`: restore: The filename parameter names exactly one metric file basename in the runner-provided writable working directory; absolute paths and directory traversal are outside the public contract. Required traces: `time`, `vin`, `done`.
- `P_FIRST_RISING_CROSSING`: restore: The first rising crossing of vin through vth is the event that records the metric and latches completion. Required traces: `time`, `vin`, `done`.
- `P_RECORDED_TIME`: restore: The metric file contains exactly one text record of the form `cross <time_seconds>` followed by a newline, where <time_seconds> is the first rising crossing time. Required traces: `time`, `vin`, `done`.
- `P_DONE_LATCH`: restore: done remains low before the first qualifying crossing and high after it, with transition smoothing set by tr. Required traces: `time`, `vin`, `done`.
- `P_SINGLE_RECORD`: restore: Later vin crossings do not clear done or create additional metric records. Required traces: `time`, `vin`, `done`.

## Modeling Constraints

- Use deterministic rising-threshold event detection and a latched completion state.
- Limit file output to the declared metric record and filename basename parameter in the runner-provided writable directory.
- Do not create waveform dumps, undeclared files, or validation-only outputs.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `file_metric_writer.va`.
Every supplied `.va` file is editable; do not add or omit files.
