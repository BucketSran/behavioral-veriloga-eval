Write a minimal voltage-domain gain extraction smoke system and one EVAS-compatible Spectre testbench.

# Task: gain_extraction_smoke

## Objective

Create a dither-based gain extraction signal path whose output differential swing is measurably
larger than the input differential swing. The checker measures waveform statistics, not an internal
estimator code.

## Required Verilog-A Modules

Return these Verilog-A modules:

1. `vin_src`
   - Ports: `clk`, `rst_n`, `vinp`, `vinn`
   - Generates a small differential voltage stimulus after reset.
2. `lfsr`
   - Ports: `dpn`, `vdd`, `vss`, `clk`, `en`, `rst_n`
   - Produces a 1-bit pseudo-random dither sign signal on `dpn`.
3. `dither_adder`
   - Ports: `vinp`, `vinn`, `dpn`, `vdin_p`, `vdin_n`
   - Adds `+/-DITHER_AMP` to the differential input according to `dpn`.
4. `gain_amp_fixed`
   - Ports: `vdin_p`, `vdin_n`, `vamp_p`, `vamp_n`
   - Applies a configurable differential gain.

Do not create a `gain_estimator` module for this task; the EVAS checker estimates gain from saved
waveforms.

## Behavioral Contract

- Use pure voltage-domain Verilog-A only.
- Use `@(cross(...))` for clocked state updates.
- Use `transition(...)` for digital-like outputs.
- `gain_amp_fixed` should support parameter `ACTUAL_GAIN`.
- `dither_adder` should support parameter `DITHER_AMP`.
- `vin_src` should support enough parameterization to generate a small clocked differential input stimulus.
- The saved waveforms must satisfy:
  - `std(vamp_p - vamp_n) / std(vinp - vinn) > 4.0`
  - `std(vamp_p - vamp_n) > std(vinp - vinn)`

## Testbench Contract

- Use a 0.9 V supply and 0 V reference.
- Drive a 50 MHz-class clock, active-low reset, and enable signal.
- Instantiate `vin_src`, `lfsr`, `dither_adder`, and `gain_amp_fixed` as a connected signal path.
- Use `ACTUAL_GAIN=8.64` and `DITHER_AMP=0.014063` or equivalent parameters that produce clear gain separation.
- Save these exact scalar names: `vinp`, `vinn`, `vamp_p`, `vamp_n`.
- Use the final transient setting provided by the injected Strict EVAS Validation Contract.

## Deliverables

Return exactly five fenced code blocks:

1. `vin_src.va`
2. `lfsr.va`
3. `dither_adder.va`
4. `gain_amp_fixed.va`
5. `tb_gain_extraction.scs`
