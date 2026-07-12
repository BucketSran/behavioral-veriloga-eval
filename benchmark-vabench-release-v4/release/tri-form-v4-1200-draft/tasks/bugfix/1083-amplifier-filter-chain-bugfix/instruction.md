# Amplifier Filter Chain Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `amplifier_filter_chain.va`:
  - Module `amplifier_filter_chain` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)
    - position 5: `preamp_mon` (output, electrical)
    - position 6: `filt1_mon` (output, electrical)
    - position 7: `filt2_mon` (output, electrical)
    - position 8: `settle_metric` (output, electrical)

## Public Parameter Contract

- `amplifier_filter_chain.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `amplifier_filter_chain.gain` defaults to `1.8` V/V; valid range: gain > 0; sets pre-filter gain about 0.45 V common mode.
- `amplifier_filter_chain.alpha` defaults to `0.3`; valid range: 0 < alpha <= 1; sets each sampled low-pass update coefficient.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_COMMON_MODE`: restore: Initialization or active-high reset returns the preamp and both filter stages near 0.45 V and leaves settle_metric low. Required traces: `time`, `rst`, `out`, `metric`, `preamp_mon`, `filt1_mon`, `filt2_mon`, `settle_metric`.
- `P_BOUNDED_PREAMP`: restore: At each rising clock edge, preamp_mon and metric equal gain times the sampled vin deviation about 0.45 V, clamped to 0 V through 0.9 V. Required traces: `time`, `clk`, `vin`, `metric`, `preamp_mon`.
- `P_FIRST_FILTER_STAGE`: restore: Filt1_mon applies the sampled first-order alpha update toward the bounded preamp target. Required traces: `time`, `clk`, `preamp_mon`, `filt1_mon`.
- `P_SECOND_FILTER_STAGE`: restore: Filt2_mon applies a second sampled alpha update toward the newly updated first-stage value, and out follows filt2_mon. Required traces: `time`, `clk`, `filt1_mon`, `filt2_mon`, `out`.
- `P_CASCADE_LAG`: restore: After a large input change, the second-stage output visibly lags the bounded preamp target while the two stage monitors preserve cascade order. Required traces: `time`, `clk`, `vin`, `preamp_mon`, `filt1_mon`, `filt2_mon`, `out`.
- `P_SETTLE_STATUS`: restore: Settle_metric is 0.9 V when the output-target error is below 0.16 V and 0.1 V while the chain is recovering. Required traces: `time`, `preamp_mon`, `out`, `settle_metric`.

## Modeling Constraints

- Use deterministic rising-edge sampled gain and two-stage low-pass state updates.
- Use smoothed voltage contributions only.
- Do not use current contributions, transistor-level devices, AC/noise analysis, continuous-time operators, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `amplifier_filter_chain.va`.
Every supplied `.va` file is editable; do not add or omit files.
