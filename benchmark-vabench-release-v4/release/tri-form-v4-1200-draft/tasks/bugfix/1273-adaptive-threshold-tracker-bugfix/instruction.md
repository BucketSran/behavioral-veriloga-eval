# Adaptive Threshold Tracker Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `adaptive_threshold_tracker.va`:
  - Module `adaptive_threshold_tracker` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `adapt` (input, electrical)
    - position 4: `trip` (output, electrical)
    - position 5: `threshold_mon` (output, electrical)
    - position 6: `margin_metric` (output, electrical)

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

The repaired bundle must satisfy every public property:

- `P_INITIALIZE_THE_STORED_THRESHOLD_TO_THRESHOLD`: restore: Initialize the stored threshold to `threshold_init`, `threshold_mon` to `threshold_init`, and the other observables to zero. On each rising clock crossing, reset the stored threshold and outputs to those initial values while `rst` is high. Otherwise compare `vin` against the previously stored threshold: drive `trip = vhi` when `V(vin) > old_threshold`, otherwise drive `trip = 0 V`. Drive `margin_metric = vhi * clip01(abs(V(vin) - old_threshold) / margin_fullscale)`. Required traces: `time`, `adapt`, `clk`, `margin_metric`, `rst`, `threshold_mon`, `trip`, `vin`.
- `P_WHEN_ADAPT_VTH_UPDATE_THE_STORED`: restore: When `adapt > vth`, update the stored threshold after the comparison using `threshold = clamp(adapt_alpha * old_threshold + (1.0 - adapt_alpha) * V(vin), threshold_min, threshold_max)`. Drive `threshold_mon` with the resulting next-sample threshold. Hold the last observable values between rising clock crossings. Required traces: `time`, `adapt`, `clk`, `margin_metric`, `rst`, `threshold_mon`, `trip`, `vin`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `adaptive_threshold_tracker.va`.
Every supplied `.va` file is editable; do not add or omit files.
