# Threshold Comparator

## Task Contract

Implement the requested Verilog-A artifact for `Threshold Comparator`.
- Form: `dut`
- Level: `L1`
- Category: `comparator_decision`
- Target artifact(s): `comparator.va`

Implement a voltage-domain single-ended threshold comparator.

## Public Verilog-A Interface

Declare module `comparator` with positional ports `VDD, VSS, VINP, VINN,
OUT_P`. All ports are electrical. `VDD` and `VSS` are supply rails, `VINP` and
`VINN` are the differential inputs, and `OUT_P` is the single-ended decision
output.

## Public Parameter Contract

Provide this overrideable public parameter:

- `tedge = 100p`: transition smoothing time for `OUT_P`.

## Required Behavior

- Initialize `OUT_P` from the initial sign of `V(VINP,VSS) - V(VINN,VSS)`.
- Drive `OUT_P` high to `VDD` when `VINP` crosses above `VINN`.
- Drive `OUT_P` low to `VSS` when `VINP` crosses below `VINN`.
- Respond to both rising and falling zero-differential crossings.
- Use finite transition-style smoothing for rail-referenced output changes.

## Modeling Constraints

Return only `comparator.va`. Use voltage contributions only. Do not modify or
emit the support harness, add validation logic, hard-code waveform sample
points, add simulator-specific side channels, use current contributions,
`ddt()`, or `idt()`. Update the retained decision state at crossing events and
drive the output contribution outside those event blocks.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `comparator.va`. Do not include explanatory prose outside the source artifact contents.
