# BBPD Data Edge Alignment Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bbpd_data_edge_alignment_ref.va`:
  - Module `bbpd_data_edge_alignment_ref` (entry)
    - position 0: `vdd` (inout, electrical)
    - position 1: `vss` (inout, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `data` (input, electrical)
    - position 4: `up` (output, electrical)
    - position 5: `dn` (output, electrical)
    - position 6: `retimed_data` (output, electrical)

## Public Parameter Contract

- `bbpd_data_edge_alignment_ref.vth` defaults to `0.45` V; valid range: finite real within the vss-to-vdd logic range; sets clk and data logic thresholds relative to vss.
- `bbpd_data_edge_alignment_ref.trf` defaults to `3e-11` s; valid range: trf > 0; sets output transition smoothing.
- `bbpd_data_edge_alignment_ref.clk_period` defaults to `2e-08` s; valid range: clk_period > 0; sets nominal full clock period for transition timing classification.
- `bbpd_data_edge_alignment_ref.clk_delay` defaults to `1e-08` s; valid range: clk_delay >= 0; sets initial nominal clock phase reference.
- `bbpd_data_edge_alignment_ref.deadzone` defaults to `8e-10` s; valid range: deadzone >= 0; sets the edge-centered pulse-suppression region.
- `bbpd_data_edge_alignment_ref.pulse_w` defaults to `1e-09` s; valid range: pulse_w > 0; sets UP or DN correction-pulse width.
- `bbpd_data_edge_alignment_ref.poll_dt` defaults to `5e-11` s; valid range: poll_dt > 0; sets pulse-expiration polling cadence.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_RETIMING`: restore: Each rising clk edge captures the current data logic level onto retimed_data, which holds between clock edges. Required traces: `time`, `clk`, `data`, `retimed_data`.
- `P_EARLY_TRANSITION_UP`: restore: A data transition closer to the upcoming nominal clock edge and outside the deadzone produces an UP pulse of pulse_w duration. Required traces: `time`, `clk`, `data`, `up`, `dn`.
- `P_LATE_TRANSITION_DN`: restore: A data transition closer to the previous nominal clock edge and outside the deadzone produces a DN pulse of pulse_w duration. Required traces: `time`, `clk`, `data`, `up`, `dn`.
- `P_DEADZONE_SUPPRESSION`: restore: Data transitions within deadzone of the relevant nominal clock edge produce neither correction pulse. Required traces: `time`, `clk`, `data`, `up`, `dn`.
- `P_BOTH_DATA_POLARITIES`: restore: Both rising and falling data transitions participate in timing classification. Required traces: `time`, `clk`, `data`, `up`, `dn`.
- `P_MUTUAL_EXCLUSION`: restore: UP and DN are mutually exclusive apart from finite analog transition overlap and use the vdd-to-vss logic range. Required traces: `time`, `vdd`, `vss`, `up`, `dn`.

## Modeling Constraints

- Use deterministic event-driven edge timing and rail-referenced voltage-coded outputs.
- Retain data only on rising clock crossings and generate bounded correction pulses.
- Do not hard-code validation waveforms or use transistor-level, AC/noise, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bbpd_data_edge_alignment_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
