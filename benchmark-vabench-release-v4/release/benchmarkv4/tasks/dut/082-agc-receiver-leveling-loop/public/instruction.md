# AGC Receiver Leveling Loop

## Task Contract

Implement the requested Verilog-A artifact for `AGC Receiver Leveling Loop`.
- Form: `dut`
- Level: `L2`
- Category: `rf_afe_behavioral_macromodels`
- Target artifact(s): `agc_receiver_leveling_loop.va`

Implement a voltage-domain automatic-gain-control receiver leveling loop.

## Public Verilog-A Interface

Declare module `agc_receiver_leveling_loop` with positional ports `clk, rst,
vin, out, metric, gain_mon, rssi_mon`. All ports are electrical.

`clk` is the gain-control update clock, `rst` is an active-high voltage-coded
reset, `vin` is the receiver input envelope centered around common mode, `out`
is the leveled receiver output, `gain_mon` exposes the bounded gain-control
state, `rssi_mon` exposes the observed output envelope, and `metric` indicates
near-target settling.

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 100p`: transition time used for smoothed voltage contributions.
- `vth = 0.45 V`: threshold for voltage-coded logic decisions.
- `target_amp = 0.18 V`: desired output-envelope amplitude around common mode.
- `deadband = 0.025 V`: tolerance band around the target amplitude before gain
  correction is needed.

## Required Behavior

On reset, initialize the gain state to `2.2`, return `out` to the 0.45 V
common-mode level, drive `rssi_mon` and `metric` to 0 V, and drive `gain_mon`
from the public gain-monitor scaling below. After reset releases, update the
sampled loop on rising `clk` crossings through `vth`.

For each non-reset update, compute the leveled output from the current gain as
`out = 0.45 + gain * (vin - 0.45)` and clamp `out` to `[0.02 V, 0.88 V]`.
The observed output envelope is `abs(out - 0.45)`. Drive `rssi_mon` as
`0.9 * envelope / 0.43`, clamped to `[0 V, 0.9 V]`. If the envelope is greater
than `target_amp + deadband`, reduce the gain by `0.18`; if the envelope is
less than `target_amp - deadband`, increase the gain by `0.10`; otherwise keep
the gain unchanged. Clamp the gain state to `[0.45, 3.0]`.

Drive `gain_mon` as `0.9 * (gain - 0.45) / (3.0 - 0.45)` after the gain
update. Drive `metric` as `0.9 - 4.0 * abs(envelope - target_amp)`, clamped to
`[0 V, 0.9 V]`. Small input envelopes should be amplified, overload windows
should reduce the gain monitor, and the output should settle toward
`target_amp` around common mode while remaining bounded.

## Modeling Constraints

Return only `agc_receiver_leveling_loop.va`. Use voltage contributions only.
Use event-updated behavioral state on the clock edge and `transition(...)`
smoothing for output contributions. Do not modify or emit the support
testbench, add validation logic, hard-code specific waveform sample points, add
simulator-specific side channels, use current contributions, transistor-level
devices, S-parameters, AC/noise-analysis behavior, communication modem
algorithms, or full link-level decoding.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `agc_receiver_leveling_loop.va`. Do not include explanatory prose outside the source artifact contents.
