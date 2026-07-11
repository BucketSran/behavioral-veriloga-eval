# Unit Element Thermometer DAC

## Task Contract

Implement the requested Verilog-A artifact for `Unit Element Thermometer DAC`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `thermometer_dac_15seg.va`

Implement a 15-segment unit-element thermometer DAC.

## Public Verilog-A Interface

Declare module `thermometer_dac_15seg` with positional ports `seg0, seg1,
seg2, seg3, seg4, seg5, seg6, seg7, seg8, seg9, seg10, seg11, seg12, seg13,
seg14, vref, vss, aout`. All ports are electrical.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: digital decision threshold for each segment input.
- `tr = 500 ps`: output transition smoothing time.

## Required Behavior

Treat every segment input above `vth` as one active unit element. Count all
fifteen unary segment pins, including `seg14`. Drive `aout` between `vss` and
`vref` in proportion to the active segment count, with zero active segments at
`vss` and all fifteen active segments at `vref`.

## Modeling Constraints

Return only `thermometer_dac_15seg.va`. Use deterministic voltage-domain
Verilog-A and smooth output transitions. Do not modify or emit the support
testbench, add validation logic, hard-code specific waveform sample points, add
simulator-specific side channels, use current contributions, `ddt()`, or
`idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `thermometer_dac_15seg.va`. Do not include explanatory prose outside the source artifact contents.
