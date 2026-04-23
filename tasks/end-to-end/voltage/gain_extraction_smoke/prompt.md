Write a Verilog-A module named `dither_adder`.

Create a voltage-domain gain extraction system in Verilog-A using dither-based
cross-correlation, then produce a minimal EVAS-compatible Spectre testbench
and run a smoke simulation.

The system consists of four connected modules:

1. **Dither adder** (`dither_adder`): adds ±DITHER_AMP to a differential input
   based on a 1-bit LFSR output (DPN); produces differential output `vdin_p/vdin_n`

2. **Fixed-gain amplifier** (`gain_amp_fixed`): differential amplifier with a
   configurable actual gain (default 8.0); output `vamp_p/vamp_n`

3. **Gain estimator** (`gain_estimator`): accumulates `vamp_diff * sign(DPN)` over
   N_TOTAL samples, then strobes the estimated gain at each power-of-2 milestone

4. **LFSR** (reuse from the digital-logic category): drives the DPN dither signal

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(cross(...))` for clock edge detection in all clocked modules
- use `transition(...)` to drive digital and bus outputs
- `vamp_p`, `vamp_n`, `vinp`, `vinn` must appear in the waveform CSV

Minimum simulation goal:

- 50 MHz clock, gain_amp ACTUAL_GAIN=8.64, DITHER_AMP=0.014063, run for at least 200 µs
- differential gain (std(vamp_diff) / std(vin_diff)) must be > 4.0
- `vamp_diff` standard deviation must be larger than `vin_diff` standard deviation

Ports:
- `VRES_P`: input electrical
- `VRES_N`: input electrical
- `DPN`: input electrical
- `VOUT_P`: output electrical
- `VOUT_N`: output electrical
