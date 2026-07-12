# Logarithmic Amplifier

## Task Contract
Implement the Verilog-A DUT `logarithmic_amplifier.va` for an offset-corrected logarithmic voltage amplifier.

## Public Verilog-A Interface
Provide `module logarithmic_amplifier(sigin, sigout);` with electrical input `sigin` and electrical output `sigout`.

## Public Parameter Contract
This task has no public parameters.

## Required Behavior
Subtract a 0.2 V input offset, take the absolute value of the adjusted voltage, floor the magnitude at 0.1 V to keep the logarithm well-defined, and drive `sigout` with the natural logarithm of that guarded magnitude.

## Modeling Constraints
Use Verilog-A real arithmetic and math operators. Do not remove the absolute value, omit the input offset or magnitude floor, use current contributions, or specialize to one waveform.

## Output Contract
Submit only the completed Verilog-A module in `logarithmic_amplifier.va`.
