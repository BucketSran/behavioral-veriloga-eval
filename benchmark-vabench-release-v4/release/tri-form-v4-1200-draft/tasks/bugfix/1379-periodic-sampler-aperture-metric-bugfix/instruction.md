# Periodic Sampler with Aperture Metric Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `periodic_sampler_aperture_metric.va`:
  - Module `periodic_sampler_aperture_metric` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `sample_en` (input, electrical)
    - position 4: `vhold` (output, electrical)
    - position 5: `aperture_metric` (output, electrical)
    - position 6: `valid` (output, electrical)

## Public Parameter Contract

- `periodic_sampler_aperture_metric.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `periodic_sampler_aperture_metric.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `periodic_sampler_aperture_metric.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `periodic_sampler_aperture_metric.aperture_gain` defaults to `0.5`; valid range: finite; overrides aperture_gain.
- `periodic_sampler_aperture_metric.tr` defaults to `120p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_CLEARS_THE_HELD_VALUE_APERTURE`: restore: Reset clears the held value, aperture metric, and valid flag. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.
- `P_ON_EACH_RISING_CLK_EDGE_WITH`: restore: On each rising `clk` edge with `sample_en` high, capture `vin` into `vhold`. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.
- `P_THE_APERTURE_METRIC_AFTER_A_CAPTURE`: restore: The aperture metric after a capture is proportional to the absolute difference between the new sample and the previous held sample. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.
- `P_HOLD_VHOLD_AND_THE_LAST_METRIC`: restore: Hold `vhold` and the last metric between enabled sampling events. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.
- `P_VALID_IS_HIGH_AFTER_THE_FIRST`: restore: `valid` is high after the first enabled sample and low during reset. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `periodic_sampler_aperture_metric.va`.
Every supplied `.va` file is editable; do not add or omit files.
