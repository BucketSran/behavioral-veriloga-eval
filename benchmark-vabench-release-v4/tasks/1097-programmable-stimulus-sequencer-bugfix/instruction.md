# Programmable Stimulus Sequencer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `programmable_stimulus_sequencer.va`:
  - Module `programmable_stimulus_sequencer` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `mode` (input, electrical)
    - position 3: `gate` (input, electrical)
    - position 4: `out` (output, electrical)
    - position 5: `metric` (output, electrical)

## Public Parameter Contract

- `programmable_stimulus_sequencer.tr` defaults to `8e-11` s; valid range: finite real; use tr >= 0 for physical transition smoothing; sets rise and fall smoothing for out and metric without changing segment selection.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_IDLE`: restore: When rst is above the 0.45 V control threshold, out is held near 0.45 V and metric is low. Required traces: `time`, `rst`, `out`, `metric`.
- `P_RAMP_MODE`: restore: For mode below 0.30 V outside reset, out produces a monotonic ramp segment from about 0.18 V toward 0.45 V and metric is near 0.20 V. Required traces: `time`, `rst`, `mode`, `out`, `metric`.
- `P_CHIRP_MODE`: restore: For mode from 0.30 V through below 0.60 V, out is a sine segment centered near 0.45 V whose instantaneous frequency increases over the segment, with metric near 0.50 V. Required traces: `time`, `rst`, `mode`, `out`, `metric`.
- `P_BURST_GATE`: restore: For mode at or above 0.60 V and gate high, out produces a deterministic PRBS-like burst between the low and high stimulus levels. Required traces: `time`, `clk`, `rst`, `mode`, `gate`, `out`.
- `P_BURST_IDLE`: restore: In burst mode with gate low, out returns near 0.45 V and metric reports the idle rather than active-burst status. Required traces: `time`, `rst`, `mode`, `gate`, `out`, `metric`.
- `P_CONTROL_DRIVEN_SELECTION`: restore: Mode and gate behavior follows the voltage-coded inputs over arbitrary legal control schedules rather than a fixed stimulus timeline. Required traces: `time`, `clk`, `rst`, `mode`, `gate`, `out`, `metric`.

## Modeling Constraints

- Use deterministic voltage-coded ramp, chirp, and gated burst generation.
- Use smoothed voltage contributions only; absolute transient time may shape public stimulus segments.
- Do not use current contributions, ddt(), idt(), transistor-level devices, waveform tables, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `programmable_stimulus_sequencer.va`.
Every supplied `.va` file is editable; do not add or omit files.
