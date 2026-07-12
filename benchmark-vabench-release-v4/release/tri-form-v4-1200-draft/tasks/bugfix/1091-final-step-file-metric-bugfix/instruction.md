# Final Step File Metric Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `final_step_file_metric_ref.va`:
  - Module `final_step_file_metric_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `ref` (input, electrical)
    - position 3: `metric_out` (output, electrical)

## Public Parameter Contract

- `final_step_file_metric_ref.vth` defaults to `0.45` V; valid range: finite real within the VSS-to-VDD logic range; sets ref rising-crossing threshold relative to VSS.
- `final_step_file_metric_ref.tedge` defaults to `2e-10` s; valid range: tedge > 0; sets metric_out transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ZERO_INITIAL_STATE`: restore: Before any qualifying ref edge, the event count and metric_out are zero. Required traces: `time`, `ref`, `metric_out`.
- `P_RISING_EDGE_COUNT`: restore: Every rising ref crossing through vth increments the retained event count exactly once; falling crossings do not. Required traces: `time`, `ref`, `metric_out`.
- `P_NORMALIZED_METRIC`: restore: Metric_out equals the VDD-to-VSS rail span multiplied by the retained event count divided by four. Required traces: `time`, `vdd`, `vss`, `ref`, `metric_out`.
- `P_EVENT_UPDATED_OUTPUT`: restore: Metric_out changes only after counted rising events and uses finite transition smoothing of the retained target. Required traces: `time`, `ref`, `metric_out`.
- `P_FINAL_TEXT_RECORD`: restore: At final_step, the module emits one text metric record to candidate.out in the simulator working directory with format count=<integer> metric=<fixed-point to three decimals>. Required traces: `time`, `ref`, `metric_out`.

## Modeling Constraints

- Use deterministic rising-crossing count state and a final_step text-metric write.
- Smooth only the retained metric target rather than a continuously varying branch expression.
- Do not generate waveform or validation artifacts or use current contributions, transistor-level devices, ddt, or idt.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `final_step_file_metric_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
