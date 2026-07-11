# Periodic Sampler with Aperture Metric

## Task Contract

Implement one Verilog-A DUT artifact for `Periodic Sampler with Aperture Metric`.

- Target artifact: `periodic_sampler_aperture_metric.va`
- Public top module: `periodic_sampler_aperture_metric`
- Task level: `L1`
- Circuit category: `sampling_memory`

## Public Verilog-A Interface

Declare module `periodic_sampler_aperture_metric` with positional electrical ports `vin, clk, rst, sample_en, vhold, aperture_metric, valid`. All ports are electrical.

`vin` is the sampled analog input. `clk`, `rst`, and `sample_en` are voltage-coded controls. `vhold` is the held sample, `aperture_metric` reports the scaled change from the previous held sample, and `valid` marks that an enabled sample has occurred.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: logic-high metric level and clipping full scale
- `vss = 0.0 V`: logic-low/reset level
- `vth = 0.45 V`: logic threshold for controls
- `aperture_gain = 0.5`: gain applied to the absolute input change metric
- `tr = 120 ps`: output transition smoothing time

## Required Behavior

- Reset clears the held value, aperture metric, and valid flag.
- On each rising `clk` edge with `sample_en` high, capture `vin` into `vhold`.
- The aperture metric after a capture is proportional to the absolute difference between the new sample and the previous held sample.
- Hold `vhold` and the last metric between enabled sampling events.
- `valid` is high after the first enabled sample and low during reset.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `periodic_sampler_aperture_metric.va`.
