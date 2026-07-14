# Adaptive Threshold Tracker Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Adaptive Threshold Tracker` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `adaptive_threshold_tracker.va`:
  - Module `adaptive_threshold_tracker` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `adapt` (input, electrical)
    - position 4: `trip` (output, electrical)
    - position 5: `threshold_mon` (output, electrical)
    - position 6: `margin_metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `adaptive_threshold_tracker` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, adapt=adapt, trip=trip, threshold_mon=threshold_mon, margin_metric=margin_metric.

## Public Parameter Contract

- `adaptive_threshold_tracker.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `adaptive_threshold_tracker.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `adaptive_threshold_tracker.threshold_init` defaults to `0.45`; valid range: finite; overrides threshold_init.
- `adaptive_threshold_tracker.threshold_min` defaults to `0.25`; valid range: finite; overrides threshold_min.
- `adaptive_threshold_tracker.threshold_max` defaults to `0.70`; valid range: finite; overrides threshold_max.
- `adaptive_threshold_tracker.adapt_alpha` defaults to `0.75`; valid range: finite; overrides adapt_alpha.
- `adaptive_threshold_tracker.margin_fullscale` defaults to `0.45`; valid range: finite; overrides margin_fullscale.
- `adaptive_threshold_tracker.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIALIZE_THE_STORED_THRESHOLD_TO_THRESHOLD`: exercise and make observable: Initialize the stored threshold to `threshold_init`, `threshold_mon` to `threshold_init`, and the other observables to zero. On each rising clock crossing, reset the stored threshold and outputs to those initial values while `rst` is high. Otherwise compare `vin` against the previously stored threshold: drive `trip = vhi` when `V(vin) > old_threshold`, otherwise drive `trip = 0 V`. Drive `margin_metric = vhi * clip01(abs(V(vin) - old_threshold) / margin_fullscale)`. Required traces: `time`, `adapt`, `clk`, `margin_metric`, `rst`, `threshold_mon`, `trip`, `vin`.
- `P_WHEN_ADAPT_VTH_UPDATE_THE_STORED`: exercise and make observable: When `adapt > vth`, update the stored threshold after the comparison using `threshold = clamp(adapt_alpha * old_threshold + (1.0 - adapt_alpha) * V(vin), threshold_min, threshold_max)`. Drive `threshold_mon` with the resulting next-sample threshold. Hold the last observable values between rising clock crossings. Required traces: `time`, `adapt`, `clk`, `margin_metric`, `rst`, `threshold_mon`, `trip`, `vin`.

The required trace names are: `time`, `adapt`, `clk`, `margin_metric`, `rst`, `threshold_mon`, `trip`, `vin`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
