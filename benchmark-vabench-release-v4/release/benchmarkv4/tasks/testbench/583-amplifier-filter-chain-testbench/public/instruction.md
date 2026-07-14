# Amplifier Filter Chain Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Amplifier Filter Chain` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `amplifier_filter_chain` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric, preamp_mon=preamp_mon, filt1_mon=filt1_mon, filt2_mon=filt2_mon, settle_metric=settle_metric.

## Public Parameter Contract

- `amplifier_filter_chain.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `amplifier_filter_chain.gain` defaults to `1.8` V/V; valid range: gain > 0; sets pre-filter gain about 0.45 V common mode.
- `amplifier_filter_chain.alpha` defaults to `0.3`; valid range: 0 < alpha <= 1; sets each sampled low-pass update coefficient.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_COMMON_MODE`: exercise and make observable: Initialization or active-high reset returns the preamp and both filter stages near 0.45 V and leaves settle_metric low. Required traces: `time`, `rst`, `out`, `metric`, `preamp_mon`, `filt1_mon`, `filt2_mon`, `settle_metric`.
- `P_BOUNDED_PREAMP`: exercise and make observable: At each rising clock edge, preamp_mon and metric equal gain times the sampled vin deviation about 0.45 V, clamped to 0 V through 0.9 V. Required traces: `time`, `clk`, `vin`, `metric`, `preamp_mon`.
- `P_FIRST_FILTER_STAGE`: exercise and make observable: Filt1_mon applies the sampled first-order alpha update toward the bounded preamp target. Required traces: `time`, `clk`, `preamp_mon`, `filt1_mon`.
- `P_SECOND_FILTER_STAGE`: exercise and make observable: Filt2_mon applies a second sampled alpha update toward the newly updated first-stage value, and out follows filt2_mon. Required traces: `time`, `clk`, `filt1_mon`, `filt2_mon`, `out`.
- `P_CASCADE_LAG`: exercise and make observable: After a large input change, the second-stage output visibly lags the bounded preamp target while the two stage monitors preserve cascade order. Required traces: `time`, `clk`, `vin`, `preamp_mon`, `filt1_mon`, `filt2_mon`, `out`.
- `P_SETTLE_STATUS`: exercise and make observable: Settle_metric is 0.9 V when the output-target error is below 0.16 V and 0.1 V while the chain is recovering. Required traces: `time`, `preamp_mon`, `out`, `settle_metric`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`, `preamp_mon`, `filt1_mon`, `filt2_mon`, `settle_metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
