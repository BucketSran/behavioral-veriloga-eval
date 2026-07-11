# Debounce Latch

## Task Contract

Implement the requested Verilog-A artifact for `Debounce Latch`.
- Form: `dut`
- Level: `L1`
- Category: `comparator_decision`
- Target artifact(s): `debounce_latch.va`

Implement a voltage-domain comparator decision debounce latch.

## Public Verilog-A Interface

Declare module `debounce_latch` with positional ports `sig, rst_n, out`. All
ports are electrical. `sig` is the noisy voltage-coded comparator decision,
`rst_n` is an active-low reset input, and `out` is the debounced decision
output.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: logic threshold for `sig` and `rst_n`.
- `vdd = 0.9 V`: logic high output level.
- `stable = 12n`: qualification time after a rising comparator-decision edge.
- `tr = 500p`: transition smoothing time for output changes.

## Required Behavior

- Initialize `out` low.
- When `rst_n` is below `vth`, force `out` low and cancel any pending
  qualification.
- When `sig` rises through `vth` while reset is released, start a qualification
  timer.
- When the qualification timer expires, set `out` high only if both `sig` and
  `rst_n` are still above `vth`.
- When `sig` falls below `vth`, clear `out` low and cancel any pending
  qualification.
- Hold the debounced output state between reset, input-edge, and timer events.

## Modeling Constraints

Return only `debounce_latch.va`. Use voltage contributions only. Do not modify
or emit the support testbench, add validation logic, hard-code waveform sample
points, add simulator-specific side channels, use current contributions,
`ddt()`, or `idt()`. For event-driven behavior, update local state in analog
event blocks and drive the output contribution outside those event blocks with
finite transition-style smoothing.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `debounce_latch.va`. Do not include explanatory prose outside the source artifact contents.
