# Comparator Offset Search

## Task Contract

Implement the requested Verilog-A artifact for `Comparator Offset Search`.
- Form: `dut`
- Level: `L2`
- Category: `comparator_decision_circuits`
- Target artifact(s): `comparator_offset_search_ref.va`

Implement `comparator_offset_search_ref.va` in Verilog-A. This is a
voltage-domain comparator characterization block: it observes a differential
input ramp, exposes the comparator decision, captures the first positive
decision trip point, and reports the measured input-referred offset.

Return the DUT/source artifact only, not a Spectre testbench. The target module
is a public measurement companion for a comparator offset-search flow, not a
validation or logging side channel.

## Public Verilog-A Interface

Declare this module:

```verilog
module comparator_offset_search_ref(vdd, vss, inp, inn, outp, trip_v, offset_est, valid);
```

All ports are electrical. `vdd` and `vss` are the supply rails. `inp` and `inn`
are the differential comparator inputs. `outp` is the voltage-coded comparator
decision. `trip_v`, `offset_est`, and `valid` are voltage-domain measurement
outputs.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vos = 5m V`: positive input-referred comparator offset threshold.
- `trf = 20p`: transition smoothing time for decision and measurement outputs.

## Required Behavior

- Initialize `valid`, `trip_v`, and `offset_est` to a zero-measurement state.
- Initialize `outp` consistently with the current differential input relative
  to `vos`.
- Drive `outp` high when `V(inp,vss) - V(inn,vss)` rises above `vos`.
- Drive `outp` low when that differential input falls back below `vos`.
- On the first positive crossing of the offset threshold, capture the input
  trip voltage on `trip_v`, capture the measured differential offset on
  `offset_est`, and assert `valid`.
- Keep the captured `trip_v`, `offset_est`, and `valid` state stable after the
  first valid measurement.
- Drive voltage-coded logic outputs rail-to-rail relative to `vdd` and `vss`
  using finite transition-style smoothing.

## Modeling Constraints

Use voltage contributions only. Do not modify or emit the support testbench,
add validation logic, hard-code waveform sample points, add validation-only hooks,
use simulator-specific side channels, instantiate transistor-level devices, use
current contributions, use AC/noise analysis, or rely on `ddt()` or `idt()`.
Update retained decision and measurement state at crossing events and drive
voltage contributions outside those event blocks.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `comparator_offset_search_ref.va`.
