# Edge Crossing Interval Timer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cross_interval_163p333_ref.va`:
  - Module `cross_interval_163p333_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `a` (input, electrical)
    - position 3: `b` (input, electrical)
    - position 4: `delay_out` (output, electrical)
    - position 5: `seen_out` (output, electrical)

## Public Parameter Contract

- `cross_interval_163p333_ref.vth` defaults to `0.45` V; valid range: finite real within the VSS-to-VDD logic range; sets rising-edge thresholds for a and b relative to VSS.
- `cross_interval_163p333_ref.scale_ps` defaults to `200.0` ps; valid range: scale_ps > 0; sets measured-delay normalization for delay_out.
- `cross_interval_163p333_ref.tedge` defaults to `2e-11` s; valid range: tedge > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_A_EDGE_ARMS`: restore: A rising a crossing arms a fresh measurement and clears seen_out until completion. Required traces: `time`, `a`, `seen_out`.
- `P_FIRST_B_EDGE_CAPTURES`: restore: The first rising b crossing after an armed a edge captures their elapsed time; b edges before arming do not complete a measurement. Required traces: `time`, `a`, `b`, `delay_out`, `seen_out`.
- `P_DELAY_NORMALIZATION`: restore: Delay_out equals the VDD-to-VSS rail span multiplied by measured delay in picoseconds divided by scale_ps. Required traces: `time`, `vdd`, `vss`, `a`, `b`, `delay_out`.
- `P_COMPLETION_MARKER`: restore: Seen_out is rail-high after a valid a-then-b capture and rail-low while a newly armed measurement is incomplete. Required traces: `time`, `vdd`, `vss`, `a`, `b`, `seen_out`.
- `P_SINGLE_CAPTURE_PER_ARM`: restore: Additional b crossings after completion do not change delay_out until the next rising a edge rearms the timer. Required traces: `time`, `a`, `b`, `delay_out`, `seen_out`.

## Modeling Constraints

- Use deterministic crossing events and retained measurement state.
- Use rail-referenced smoothed voltage outputs only.
- Do not hard-code validation intervals or use waveform files, transistor-level devices, AC/noise analysis, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cross_interval_163p333_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
