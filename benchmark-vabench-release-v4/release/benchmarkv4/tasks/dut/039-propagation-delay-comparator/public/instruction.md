# Propagation Delay Comparator

## Task Contract

Implement the requested Verilog-A artifact for `Propagation Delay Comparator`.
- Form: `dut`
- Level: `L1`
- Category: `comparator_decision`
- Target artifact(s): `cmp_delay.va`, `edge_interval_timer.va`

Implement a voltage-domain clocked comparator whose clock-to-output delay grows
as the effective differential input becomes smaller, plus the supplied timing
helper artifact.

## Public Verilog-A Interface

Return these Verilog-A artifacts:

- `cmp_delay.va`: declares module `cmp_delay` with positional ports `CLK, VINN,
  VINP, DCMPN, DCMPP, LP, LM, VSS, VDD`.
- `edge_interval_timer.va`: declares module `edge_interval_timer` with
  positional ports `CLK_1, CLK_2, OUT_PS`.

All ports are electrical. In `cmp_delay`, `CLK` is the comparator clock,
`VINP`/`VINN` are the differential inputs, `DCMPP`/`DCMPN` are complementary
decision outputs, `LP`/`LM` mirror the positive and negative decision outputs
as compatibility monitor outputs, and `VSS`/`VDD` are supply rails. In
`edge_interval_timer`, `OUT_PS` reports a measured edge
interval in picoseconds as a voltage-coded real value.

## Public Parameter Contract

For `cmp_delay`, provide these overrideable public parameters:

- `voffset = 0`: input-referred offset subtracted from `VINP - VINN`.
- `tau = 4.34e-12`: regeneration time constant.
- `td_0 = 20.5e-12`: base delay offset.
- `td_min = 20e-12`: minimum comparator delay.
- `td_max = 200e-12`: maximum comparator delay.

For `edge_interval_timer`, provide `VTH = 0.4 V` as the edge-detection
threshold.

## Required Behavior

- Initialize the comparator decision outputs low.
- Use `V(VDD,VSS)/2` as the comparator clock threshold.
- On each rising clock crossing, latch the sign of
  `V(VINP,VSS) - V(VINN,VSS) - voffset`.
- Schedule the decision outputs using a log-linear regeneration delay:
  compute `vdiff_eff = abs(V(VINP,VSS) - V(VINN,VSS) - voffset)`, floor it at
  a small positive value to avoid `ln(0)`, compute
  `td_raw = td_0 + tau * ln(V(VDD,VSS) / vdiff_eff)`, and clamp the result to
  `[td_min, td_max]`.
- On each falling clock crossing, reset the comparator decision outputs low.
- Drive `LP` with the same delayed voltage-coded state as `DCMPP` and `LM`
  with the same delayed voltage-coded state as `DCMPN`.
- Drive the timing helper so it captures the time between rising crossings of
  `CLK_1` and `CLK_2`, converts that interval to picoseconds, and holds the
  most recent completed measurement on `OUT_PS`.

## Modeling Constraints

Return only `cmp_delay.va` and `edge_interval_timer.va`. Use voltage
contributions only. Do not modify or emit the support testbench, add validation
logic, hard-code waveform sample points, add simulator-specific side channels,
use current contributions, `ddt()`, or `idt()`. Update event-driven state in
analog event blocks and place voltage contributions outside those event blocks.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly the requested source artifact(s): `cmp_delay.va`, `edge_interval_timer.va`. Do not include explanatory prose outside the source artifact contents.
