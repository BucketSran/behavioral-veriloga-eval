# Smooth Comparator Tanh

## Task Contract

Implement the requested Verilog-A artifact for `Smooth Comparator Tanh`.
- Form: `dut`
- Level: `L1`
- Category: `comparator`
- Target artifact(s): `smooth_comparator_tanh.va`

Implement a pure voltage-domain smooth comparator based on a tanh transfer.

## Public Verilog-A Interface

Declare module `smooth_comparator_tanh` with positional ports `sigin, sigref,
sigout`. All ports are electrical.

## Public Parameter Contract

Provide these overrideable public parameters:

- `high = 1.0 V`: upper output level.
- `low = -1.0 V`: lower output level.
- `offset = 0.0 V`: input-referred offset applied to `V(sigin,sigref)`.
- `comp_slope = 1000.0 1/V`: tanh slope coefficient.

## Required Behavior

- `P_TANH_TRANSFER`: Drive `sigout` as `0.5 * (high - low) * tanh(comp_slope * (V(sigin, sigref) - offset)) + 0.5 * (high + low)`.

- `P_INPUT_POLARITY`: A larger `V(sigin, sigref)` must move the output toward `high`, not toward `low`.

- `P_SMOOTH_TRANSITION`: The output must transition smoothly between `low` and `high` according to the tanh slope, not as a hard switch.

## Modeling Constraints

Return only `smooth_comparator_tanh.va`. Use voltage contributions only. Do not
modify or emit the support testbench, add validation logic, hard-code waveform
sample points, add simulator-specific side channels, use current contributions,
`ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `smooth_comparator_tanh.va`. Do not include explanatory prose outside the source artifact contents.
