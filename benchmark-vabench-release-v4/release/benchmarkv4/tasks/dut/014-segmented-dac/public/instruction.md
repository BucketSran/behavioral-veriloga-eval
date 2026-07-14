# Segmented DAC

## Task Contract

Implement the requested Verilog-A artifact for `Segmented DAC`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `segmented_dac.va`

Implement a mixed binary/thermometer segmented voltage DAC.

## Public Verilog-A Interface

Declare module `segmented_dac` with positional ports `b0, b1, t0, t1, t2,
vref, vss, aout`. All ports are electrical.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: digital decision threshold for binary and thermometer
  controls.
- `tr = 500 ps`: output transition smoothing time.

## Required Behavior

Treat `b0` and `b1` as binary LSB controls with weights 1 and 2. Treat
`t0`, `t1`, and `t2` as unary thermometer segment controls, each contributing
four LSB steps. Drive `aout` between `vss` and `vref` according to the summed
15-step segmented code, so the all-active code reaches full scale.

## Modeling Constraints

Return only `segmented_dac.va`. Use deterministic voltage-domain Verilog-A and
smooth output transitions. Do not modify or emit the support testbench, add
validation logic, hard-code specific waveform sample points, add simulator-specific
side channels, use current contributions, `ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `segmented_dac.va`. Do not include explanatory prose outside the source artifact contents.
