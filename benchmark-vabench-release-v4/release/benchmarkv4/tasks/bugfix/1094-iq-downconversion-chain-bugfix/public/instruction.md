# IQ Downconversion Chain Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `iq_downconversion_chain.va`:
  - Module `iq_downconversion_chain` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)
    - position 5: `lo_i` (output, electrical)
    - position 6: `lo_q` (output, electrical)
    - position 7: `mix_i` (output, electrical)
    - position 8: `mix_q` (output, electrical)
    - position 9: `phase_mon` (output, electrical)

## Public Parameter Contract

- `iq_downconversion_chain.tr` defaults to `8e-11` s; valid range: tr > 0; sets output transition smoothing.
- `iq_downconversion_chain.vth` defaults to `0.45` V; valid range: finite real; sets clock and reset logic threshold.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_COMMON_MODE`: restore: Active-high reset returns I/Q baseband outputs, LO monitors, and mixer monitors to 0.45 V and phase_mon to 0.9 V. Required traces: `time`, `rst`, `out`, `metric`, `lo_i`, `lo_q`, `mix_i`, `mix_q`, `phase_mon`.
- `P_QUADRATURE_SEQUENCE`: restore: Successive non-reset rising clk edges cycle the I/Q coefficient pairs through (1,0), (0,1), (-1,0), and (0,-1), then wrap. Required traces: `time`, `clk`, `rst`, `lo_i`, `lo_q`, `phase_mon`.
- `P_LO_MONITORS`: restore: Lo_i and lo_q equal 0.45 V plus 0.40 V times their current quadrature coefficients. Required traces: `time`, `lo_i`, `lo_q`, `phase_mon`.
- `P_MIXER_MONITORS`: restore: Each mixer monitor equals 0.45 V plus 1.25 times the vin deviation times its LO coefficient, clamped to 0.02 V through 0.88 V. Required traces: `time`, `vin`, `lo_i`, `lo_q`, `mix_i`, `mix_q`.
- `P_BASEBAND_UPDATES`: restore: On each valid edge, out and metric apply the public 0.85 first-order update toward mix_i and mix_q respectively and remain clamped to 0.02 V through 0.88 V. Required traces: `time`, `clk`, `mix_i`, `mix_q`, `out`, `metric`.
- `P_PHASE_MONITOR`: restore: Phase_mon exposes the current four-state phase as phase/3 times 0.9 V. Required traces: `time`, `clk`, `phase_mon`.

## Modeling Constraints

- Use deterministic rising-edge four-state quadrature and sampled baseband state.
- Use bounded smoothed voltage contributions only.
- Do not use transistor-level devices, S-parameters, AC/noise analysis, communication decoding, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `iq_downconversion_chain.va`.
Every supplied `.va` file is editable; do not add or omit files.
