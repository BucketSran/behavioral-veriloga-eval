# Differential Deadband Amplifier

## Task Contract

Implement the requested Verilog-A artifact for `Differential Deadband`.
- Form: `dut`
- Level: `L1`
- Category: `mixed_signal`
- Target artifact(s): `differential_deadband.va`

Implement `differential_deadband` in `differential_deadband.va`.

The module is a voltage-domain DUT with port order `sigin_p, sigin_n, sigout`.
Declare all ports as `electrical`; `sigin_p` and `sigin_n` are inputs and
`sigout` is the output.

Use the differential input voltage from `sigin_p` to `sigin_n`. Inside the
deadband window, including the two thresholds, drive the leakage output level.
Below the lower threshold, drive the low-side signed differential residue
scaled by `gain` and offset by the leakage level. Above the upper threshold,
drive the high-side signed differential residue scaled by the same `gain` and
offset by the leakage level. Preserve differential polarity and continuity at
the deadband boundaries.

Provide overridable real parameters `dead_low=-0.1`, `dead_high=0.1`, `gain=1`,
and `leak=0`. The threshold and leakage values are voltages; `gain` is
dimensionless.

## Public Verilog-A Interface

The file `differential_deadband.va` must define `module differential_deadband(sigin_p, sigin_n, sigout);`. All ports are electrical. `sigin_p` and `sigin_n` form the differential signed input and `sigout` is the deadbanded output.

## Public Parameter Contract

The public parameters declared by `differential_deadband.va` are part of the contract and may be overridden by validation harnesses:

- `parameter real dead_high = 0.1;`
- `parameter real dead_low = -0.1;`
- `parameter real gain = 1;`
- `parameter real leak = 0;`

## Required Behavior

- `P_DIFFERENTIAL_INPUT`: Use `V(sigin_p, sigin_n)` as the signed input error; do not collapse the transfer to one input terminal.

- `P_LEAK_INSIDE_DEADBAND`: For `dead_low <= V(sigin_p, sigin_n) <= dead_high`, drive `sigout` to the parameter `leak`.

- `P_GAINED_RESIDUE_OUTSIDE_DEADBAND`: Below `dead_low`, drive `gain * (diff - dead_low) + leak`; above `dead_high`, drive `gain * (diff - dead_high) + leak`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `differential_deadband.va`. Do not include explanatory prose outside the source artifact contents.
