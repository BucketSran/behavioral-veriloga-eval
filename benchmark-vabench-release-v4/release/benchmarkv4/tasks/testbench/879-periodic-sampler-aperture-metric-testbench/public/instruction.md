# Periodic Sampler with Aperture Metric Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Periodic Sampler with Aperture Metric` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `periodic_sampler_aperture_metric.va`:
  - Module `periodic_sampler_aperture_metric` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `sample_en` (input, electrical)
    - position 4: `vhold` (output, electrical)
    - position 5: `aperture_metric` (output, electrical)
    - position 6: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `periodic_sampler_aperture_metric` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, sample_en=sample_en, vhold=vhold, aperture_metric=aperture_metric, valid=valid.

## Public Parameter Contract

- `periodic_sampler_aperture_metric.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `periodic_sampler_aperture_metric.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `periodic_sampler_aperture_metric.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `periodic_sampler_aperture_metric.aperture_gain` defaults to `0.5`; valid range: finite; overrides aperture_gain.
- `periodic_sampler_aperture_metric.tr` defaults to `120p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_CLEARS_THE_HELD_VALUE_APERTURE`: exercise and make observable: Reset clears the held value, aperture metric, and valid flag. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.
- `P_ON_EACH_RISING_CLK_EDGE_WITH`: exercise and make observable: On each rising `clk` edge with `sample_en` high, capture `vin` into `vhold`. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.
- `P_THE_APERTURE_METRIC_AFTER_A_CAPTURE`: exercise and make observable: The aperture metric after a capture is proportional to the absolute difference between the new sample and the previous held sample. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.
- `P_HOLD_VHOLD_AND_THE_LAST_METRIC`: exercise and make observable: Hold `vhold` and the last metric between enabled sampling events. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.
- `P_VALID_IS_HIGH_AFTER_THE_FIRST`: exercise and make observable: `valid` is high after the first enabled sample and low during reset. Required traces: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `sample_en`, `vhold`, `aperture_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
