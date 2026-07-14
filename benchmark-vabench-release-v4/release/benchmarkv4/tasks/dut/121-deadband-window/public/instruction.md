# Deadband Window

## Task Contract

Implement the requested Verilog-A artifact for `Deadband Window`.
- Form: `dut`
- Level: `L1`
- Category: `mixed_signal`
- Target artifact(s): `deadband_window.va`

Implement `deadband_window` in `deadband_window.va`.

The module is a voltage-domain DUT with port order `sigin, sigout`. Declare
both ports as `electrical`; `sigin` is the input and `sigout` is the output.

Treat `V(sigin)` as a signed error signal. Drive `sigout` to zero when the
input is within the deadband window, including the two thresholds. Below the
lower threshold, drive the signed residue relative to the lower edge. Above the
upper threshold, drive the signed residue relative to the upper edge. The output
should be continuous at both deadband boundaries.

Provide overridable real parameters `dead_low=-0.1` and `dead_high=0.1`, in
volts, and use the instance-provided values when they are overridden.

## Public Verilog-A Interface

The file `deadband_window.va` must define `module deadband_window(sigin, sigout);`. Both ports are electrical. `sigin` is the signed error input and `sigout` is the deadbanded output.

## Public Parameter Contract

The public parameters declared by `deadband_window.va` are part of the contract and may be overridden by validation harnesses:

- `parameter real dead_high = 0.1;`
- `parameter real dead_low = -0.1;`

## Required Behavior

- `P_ZERO_INSIDE_DEADBAND`: For `dead_low <= V(sigin) <= dead_high`, drive `sigout` to 0 V.

- `P_LOWER_RESIDUE`: For `V(sigin) < dead_low`, drive `sigout` to `V(sigin) - dead_low`.

- `P_UPPER_RESIDUE`: For `V(sigin) > dead_high`, drive `sigout` to `V(sigin) - dead_high`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `deadband_window.va`. Do not include explanatory prose outside the source artifact contents.
