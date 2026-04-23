Given a 4-bit segmented DAC with 2 thermometer-style MSBs and 2 binary LSBs,
write a minimal Spectre-compatible testbench that scans all codes, highlights
boundary transitions such as `3->4`, `7->8`, and `11->12`, and saves the output
waveform for glitch/monotonicity inspection.

Ports:
- `vdd`: inout electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `d3`: input electrical
- `d2`: input electrical
- `d1`: input electrical
- `d0`: input electrical
- `vout`: output electrical

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`

DUT module to instantiate: `segmented_dac_glitch_ref`
