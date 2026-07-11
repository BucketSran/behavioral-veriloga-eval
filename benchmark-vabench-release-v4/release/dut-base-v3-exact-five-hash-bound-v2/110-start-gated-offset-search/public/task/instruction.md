# Start Gated Offset Search

## Task Contract

Implement the requested Verilog-A artifact for `Start Gated Offset Search`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `start_gated_offset_search.va`

Implement a standalone start-gated comparator-offset calibration search driver
for a converter calibration loop.

## Public Verilog-A Interface

Declare module `start_gated_offset_search` with positional ports `CLK, VOUT,
START, VINP, VINN`. All ports are electrical. `VINP` and `VINN` are the
differential calibration stimulus outputs.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: logic high and decision reference scale.
- `vcm = 0.7 V`: common-mode voltage for `VINP` and `VINN`.
- `vstart_th = 0.45 V`: decision threshold for `START`.

## Required Behavior

Before `START` is asserted, hold both outputs at `vcm` and reset the search
state to differential value `0`, step `20 mV`, and high direction. On each
rising `START` crossing through `vstart_th`, reinitialize the same search
state. When `START` falls below `vstart_th`, disable the search and return both
outputs to `vcm`.

While `START` is high, update the search only on falling `CLK` crossings through
`0.5 * vdd`. Use that same `0.5 * vdd` threshold for the comparator decision:
treat `VOUT > 0.5 * vdd` as the high decision direction and `VOUT <= 0.5 * vdd`
as the low decision direction. If the newly sampled direction differs from the
previous search direction, halve the current step before moving. Then update
the differential search value by `+step` for the high direction or `-step` for
the low direction, and remember the sampled direction for the next update.

Drive `VINP = vcm + 0.5 * differential_value` and
`VINN = vcm - 0.5 * differential_value` while the search is enabled. This keeps
the output common mode at `vcm` and makes `VINP - VINN` equal to the accumulated
differential search value.

## Modeling Constraints

Return only `start_gated_offset_search.va`. Use deterministic voltage-domain
Verilog-A. Do not modify or emit the provided testbench, add validation logic,
hard-code specific waveform sample points, add simulator-specific side channels,
use current contributions, `ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `start_gated_offset_search.va`. Do not include explanatory prose outside the source artifact contents.
