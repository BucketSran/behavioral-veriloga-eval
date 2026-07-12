# Hysteresis Trip Characterizer

## Task Contract

Implement the requested Verilog-A artifact for `Hysteresis Trip Characterizer`.
- Form: `dut`
- Level: `L2`
- Category: `comparator`
- Target artifact(s): `hysteresis_trip_characterizer.va`
- Public support artifact(s): `support_hysteretic_comparator.va`

Implement a voltage-domain measurement component that observes a comparator
input ramp and output decision waveform, captures the observable rising and
falling trip voltages, and reports the hysteresis width.

## Public Verilog-A Interface

Declare module `hysteresis_trip_characterizer` with positional ports `vdd, vss,
vin, cmp_out, trip_rise, trip_fall, hyst_width, valid`. All ports are
electrical. `vin` is the swept input being characterized, `cmp_out` is the
rail-coded comparator output, `trip_rise` and `trip_fall` are voltage-coded
captured trip points, `hyst_width` is the signed difference
`trip_rise - trip_fall`, and `valid` is a rail-coded flag that asserts after
both trip directions have been observed.

## Public Parameter Contract

Provide this overrideable public parameter:

- `tr = 20p`: output transition time for reported measurement voltages.

## Required Behavior

- Use the midpoint between `vdd` and `vss` as the decision threshold for
  `cmp_out`.
- When `cmp_out` rises through the midpoint, capture the instantaneous
  `vin - vss` value into `trip_rise`.
- When `cmp_out` falls through the midpoint, capture the instantaneous
  `vin - vss` value into `trip_fall`.
- Continue updating the captured values on later output transitions.
- Drive `hyst_width` as `trip_rise - trip_fall` once both captures are present.
- Drive `valid` low until both directions have been captured, then drive it
  high.

## Modeling Constraints

Return only `hysteresis_trip_characterizer.va`. Use deterministic
voltage-domain Verilog-A and voltage contributions only. The hysteretic
comparator under measurement is a supplied support artifact, not part of the
returned DUT. Do not modify or emit the support testbench, add validation logic,
hard-code waveform sample points, add simulator-specific side channels, use
current contributions, `ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `hysteresis_trip_characterizer.va`. Do not include explanatory prose outside the source artifact contents.
