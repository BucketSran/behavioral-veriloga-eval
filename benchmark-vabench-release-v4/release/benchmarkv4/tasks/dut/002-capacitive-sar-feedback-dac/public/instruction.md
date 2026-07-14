# Capacitive SAR Feedback DAC

## Task Contract

Implement the requested Verilog-A artifact for `Capacitive Weighted SAR Feedback DAC`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `cdac_cal.va`

Implement a clocked capacitive feedback DAC for a SAR ADC.

## Public Verilog-A Interface

Declare module `cdac_cal` with positional ports `VDD, VSS, CLK, D9, D8, D7,
D6, D5, D4, D3, D2, D1, D0, CAL0, CAL1, VDAC_P, VDAC_N`. All ports are
electrical. `VDD` and `VSS` are supply/reference nodes; `VDAC_P` and `VDAC_N`
are complementary differential outputs.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vcm = 0.45 V`: output common-mode voltage.
- `swing = 0.6 V`: differential output swing scale.
- `tt = 20 ps`: output transition smoothing time.

Use a 0.45 V logic threshold for the sampled clock, DAC control bits, and
calibration bits.

## Required Behavior

On each rising `CLK` edge, sample `D9..D0`, `CAL0`, and `CAL1`. Interpret
`D9..D0` as an unsigned 10-bit binary word with `D9` as the most significant
bit and `D0` as the least significant bit. Interpret the calibration pins as a
small unsigned code where `CAL0` contributes one unit and `CAL1` contributes
two units.

Model the redundant calibration contribution as an additive offset of 32 main
DAC codes per calibration unit. Higher effective code should raise `VDAC_P`
relative to `VDAC_N`; lower effective code should lower it. Drive complementary
outputs around `vcm`, with the output differential proportional to the centered
effective code over the full 10-bit main-code range.

## Modeling Constraints

Return only `cdac_cal.va`. Use deterministic voltage-domain Verilog-A and
smooth output transitions. Do not modify or emit the support testbench, add
validation logic, hard-code specific waveform sample points, add simulator-specific
side channels, use current contributions, `ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `cdac_cal.va`. Do not include explanatory prose outside the source artifact contents.
