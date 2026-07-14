# Comparator Offset Calibration Loop

## Task Contract

Implement the requested Verilog-A artifact for `Comparator Offset Calibration Loop`.
- Form: `dut`
- Level: `L2`
- Category: `comparator`
- Target artifact(s): `comparator_offset_calibration_loop.va`
- Public support artifact(s): `support_offset_comparator.va`

Implement a voltage-domain calibration loop that drives a comparator with a
successive-approximation differential stimulus and reports the estimated input
offset after the search completes.

## Public Verilog-A Interface

Declare module `comparator_offset_calibration_loop` with positional ports `vdd,
vss, clk, dcmpp, vinp, vinn, offset_est, valid`. All ports are electrical.
`clk` is the update clock, `dcmpp` is the sampled comparator decision input,
`vinp`/`vinn` are the generated differential stimulus outputs, `offset_est` is
the signed voltage-coded offset estimate, and `valid` is a rail-coded completion
flag.

## Public Parameter Contract

Provide these overrideable public parameters:

- `step_initial = 64m V`: initial differential search step.
- `iterations = 7`: number of falling-clock updates before the estimate is
  reported valid.
- `tr = 20p`: output transition time for generated analog outputs.

## Required Behavior

- Initialize the signed differential estimate to zero and the search step to
  `step_initial`.
- On each falling crossing of `clk` through the midpoint between `vdd` and
  `vss`, sample `dcmpp`.
- A high sampled decision means the applied differential stimulus is above the
  comparator trip point, so the loop decreases the estimate by the current
  search step. A low sampled decision means the loop increases the estimate by
  the current search step.
- Halve the search step after every update.
- Drive `vinp` and `vinn` symmetrically around mid-supply so that `vinp - vinn`
  equals the current estimate.
- Drive `offset_est` with the current signed estimate. Drive `valid` low until
  the configured number of updates has completed, then drive it high.

## Modeling Constraints

Return only `comparator_offset_calibration_loop.va`. Use deterministic
voltage-domain Verilog-A and voltage contributions only. The companion
comparator model is a supplied support artifact, not part of the returned DUT.
Do not modify or emit the support testbench, add validation logic, hard-code
waveform sample points, add simulator-specific side channels, use current
contributions, `ddt()`, or `idt()`. Update calibration state in analog event
blocks and drive voltage outputs outside those event blocks.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `comparator_offset_calibration_loop.va`. Do not include explanatory prose outside the source artifact contents.
