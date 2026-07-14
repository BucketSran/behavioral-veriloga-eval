# Pipeline ADC Stage

## Task Contract

Implement the requested Verilog-A artifact for `Pipeline ADC Stage`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `pipeline_stage.va`

Implement a clocked 1.5-bit pipeline ADC MDAC stage.

## Public Verilog-A Interface

Declare module `pipeline_stage` with positional ports `VDD, VSS, PHI1, PHI2,
VIN, VREF, VRES, D1, D0`. All ports are electrical. `VRES` is the residue
output and `D1,D0` are the sub-ADC decision outputs.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: clock decision threshold for `PHI1` and `PHI2`.
- `vdd = 0.9 V`: nominal output high level used for initialization.
- `tedge = 200 ps`: output transition smoothing time.

## Required Behavior

On each rising `PHI1` edge, sample `VIN`. On each rising `PHI2` edge, compare
the sampled input around `V(VDD)/2` against the 1.5-bit thresholds
`+V(VREF)/4` and `-V(VREF)/4`.

- Upper region: drive `D1` high, `D0` low, and subtract a half-reference from
  the gain-two residue.
- Middle region: drive `D1` low, `D0` high, and use the gain-two residue
  without reference subtraction or addition.
- Lower region: drive both decision outputs low and add a half-reference to the
  gain-two residue.

Clamp `VRES` to the supply range and drive all outputs with smooth
voltage-domain transitions.

## Modeling Constraints

Return only `pipeline_stage.va`. Use deterministic voltage-domain Verilog-A.
Do not modify or emit the support testbench, add validation logic, hard-code
specific waveform sample points, add simulator-specific side channels, use
current contributions, `ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `pipeline_stage.va`. Do not include explanatory prose outside the source artifact contents.
