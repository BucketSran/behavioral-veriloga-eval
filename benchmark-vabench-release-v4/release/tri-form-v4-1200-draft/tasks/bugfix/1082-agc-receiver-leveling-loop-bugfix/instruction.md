# AGC Receiver Leveling Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `agc_receiver_leveling_loop.va`:
  - Module `agc_receiver_leveling_loop` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)
    - position 5: `gain_mon` (output, electrical)
    - position 6: `rssi_mon` (output, electrical)

## Public Parameter Contract

- `agc_receiver_leveling_loop.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `agc_receiver_leveling_loop.vth` defaults to `0.45` V; valid range: finite real; sets clk and reset logic threshold.
- `agc_receiver_leveling_loop.target_amp` defaults to `0.18` V; valid range: 0 <= target_amp <= 0.43; sets desired output-envelope amplitude about common mode.
- `agc_receiver_leveling_loop.deadband` defaults to `0.025` V; valid range: deadband >= 0; sets the no-adjustment envelope tolerance.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_STATE`: restore: Active-high reset restores out to 0.45 V, clears rssi_mon and metric, and represents the initial gain 2.2 on gain_mon. Required traces: `time`, `rst`, `out`, `metric`, `gain_mon`, `rssi_mon`.
- `P_CLOCKED_GAIN_LOOP`: restore: The AGC samples and updates its held output and gain state only on rising clk crossings after reset releases. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `gain_mon`.
- `P_OUTPUT_ENVELOPE`: restore: Out is the current-gain amplification of vin about 0.45 V, clamped to 0.02 V through 0.88 V, and rssi_mon reports the normalized absolute output envelope. Required traces: `time`, `clk`, `vin`, `out`, `rssi_mon`.
- `P_GAIN_DIRECTION_AND_BOUNDS`: restore: Envelope above target_amp plus deadband lowers gain by 0.18, envelope below target_amp minus deadband raises gain by 0.10, and gain remains in 0.45 through 3.0. Required traces: `time`, `clk`, `out`, `gain_mon`, `rssi_mon`.
- `P_DEADBAND_HOLD`: restore: When the observed envelope lies within the target deadband, the bounded gain state holds across the update. Required traces: `time`, `clk`, `out`, `gain_mon`, `rssi_mon`.
- `P_SETTLING_METRIC`: restore: Metric decreases with absolute envelope error from target_amp according to the public scaling and remains clamped to 0 V through 0.9 V. Required traces: `time`, `out`, `metric`, `rssi_mon`.

## Modeling Constraints

- Use deterministic rising-edge event-updated gain-control state.
- Use smoothed voltage contributions only.
- Do not use current contributions, transistor-level, AC/noise, link-level decoding, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `agc_receiver_leveling_loop.va`.
Every supplied `.va` file is editable; do not add or omit files.
