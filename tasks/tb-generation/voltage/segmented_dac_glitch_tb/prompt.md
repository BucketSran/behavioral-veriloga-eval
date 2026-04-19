Given a 4-bit segmented DAC with 2 thermometer-style MSBs and 2 binary LSBs,
write a minimal Spectre-compatible testbench that scans all codes, highlights
boundary transitions such as `3->4`, `7->8`, and `11->12`, and saves the output
waveform for glitch/monotonicity inspection.
