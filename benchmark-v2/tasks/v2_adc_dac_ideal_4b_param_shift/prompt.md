# Task: Clocked 4-bit ADC + DAC Reconstruction (Parameter-Shift Variant)

Write EVAS-compatible Verilog-A modules for a 4-bit ADC followed by a 4-bit DAC reconstruction path, under shifted supply/timing parameters.

## Required output file

- `dut.va`

## Module requirements

Your `dut.va` must define:

1. `adc_ideal_4b_renamed`
2. `dac_ideal_4b_renamed`

Ports:

- ADC inputs: `analog_in`, `sample_event`, `vdd`, `vss`, `rst_n`
- ADC outputs: `q3..q0`
- DAC inputs: `q3..q0`, `vdd`, `vss`, `rst_n`
- DAC output: `recon_level`

## Behavior

1. ADC samples `analog_in` on rising edge of `sample_event`.
2. ADC quantizes to 4-bit binary code `[0..15]`.
3. DAC reconstructs `recon_level` from that code.
4. Keep implementation pure voltage-domain and EVAS-compatible.
5. Use parameters compatible with `vdd=1.0` and 1 GHz class clocking.

## Negative constraints

1. Do not use current-domain contributions.
2. Do not use `ddt()`.
3. Do not hardcode output code without sampling.
