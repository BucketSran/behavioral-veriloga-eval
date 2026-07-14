# AGC Receiver Leveling Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `AGC Receiver Leveling Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `agc_receiver_leveling_loop.va`:
  - Module `agc_receiver_leveling_loop` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)
    - position 5: `gain_mon` (output, electrical)
    - position 6: `rssi_mon` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `agc_receiver_leveling_loop` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric, gain_mon=gain_mon, rssi_mon=rssi_mon.

## Public Parameter Contract

- `agc_receiver_leveling_loop.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `agc_receiver_leveling_loop.vth` defaults to `0.45` V; valid range: finite real; sets clk and reset logic threshold.
- `agc_receiver_leveling_loop.target_amp` defaults to `0.18` V; valid range: 0 <= target_amp <= 0.43; sets desired output-envelope amplitude about common mode.
- `agc_receiver_leveling_loop.deadband` defaults to `0.025` V; valid range: deadband >= 0; sets the no-adjustment envelope tolerance.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_STATE`: exercise and make observable: Active-high reset restores out to 0.45 V, clears rssi_mon and metric, and represents the initial gain 2.2 on gain_mon. Required traces: `time`, `rst`, `out`, `metric`, `gain_mon`, `rssi_mon`.
- `P_CLOCKED_GAIN_LOOP`: exercise and make observable: The AGC samples and updates its held output and gain state only on rising clk crossings after reset releases. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `gain_mon`.
- `P_OUTPUT_ENVELOPE`: exercise and make observable: Out is the current-gain amplification of vin about 0.45 V, clamped to 0.02 V through 0.88 V, and rssi_mon reports the normalized absolute output envelope. Required traces: `time`, `clk`, `vin`, `out`, `rssi_mon`.
- `P_GAIN_DIRECTION_AND_BOUNDS`: exercise and make observable: Envelope above target_amp plus deadband lowers gain by 0.18, envelope below target_amp minus deadband raises gain by 0.10, and gain remains in 0.45 through 3.0. Required traces: `time`, `clk`, `out`, `gain_mon`, `rssi_mon`.
- `P_DEADBAND_HOLD`: exercise and make observable: When the observed envelope lies within the target deadband, the bounded gain state holds across the update. Required traces: `time`, `clk`, `out`, `gain_mon`, `rssi_mon`.
- `P_SETTLING_METRIC`: exercise and make observable: Metric decreases with absolute envelope error from target_amp according to the public scaling and remains clamped to 0 V through 0.9 V. Required traces: `time`, `out`, `metric`, `rssi_mon`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`, `gain_mon`, `rssi_mon`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
