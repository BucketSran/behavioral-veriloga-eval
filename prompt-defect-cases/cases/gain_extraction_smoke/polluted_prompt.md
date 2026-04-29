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
- Use the final transient setting listed in the Public Evaluation Contract below.

## Deliverables

Return exactly five fenced code blocks:

1. `vin_src.va`
2. `lfsr.va`
3. `dither_adder.va`
4. `gain_amp_fixed.va`
5. `tb_gain_extraction.scs`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=200u maxstep=8n
```

Required public waveform columns in `tran.csv`:

- `vinp`, `vinn`, `vamp_p`, `vamp_n`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset`, `rst_n` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Enable-like input(s) `en`, `enable` must be in the enabled state during the post-reset checking window unless the task explicitly asks for disabled intervals.
- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clk`, `rst_n`, `en`.
